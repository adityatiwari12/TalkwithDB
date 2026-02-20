"""
Scalable Schema Manager for Chat with SQL system.
Handles incremental schema updates and table-level chunking.
"""

import json
import hashlib
import os
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from chat_sql.config import config
from chat_sql.db.connection import db_connection


@dataclass
class TableSnapshot:
    """Snapshot of a table's schema."""
    name: str
    columns: List[Dict]
    row_count: int
    checksum: str
    last_updated: datetime


@dataclass
class SchemaSnapshot:
    """Complete database schema snapshot."""
    tables: List[TableSnapshot]
    checksum: str
    created_at: datetime


class SchemaDiff:
    """Represents differences between schema versions."""
    
    def __init__(self):
        self.added_tables: List[str] = []
        self.modified_tables: List[str] = []
        self.removed_tables: List[str] = []
        self.unchanged_tables: List[str] = []


class SchemaManager:
    """
    Manages schema snapshots and incremental updates.
    
    Key features:
    - Persistent schema snapshots
    - Incremental diff detection
    - Table-level change tracking
    - Minimal re-embedding requirements
    """
    
    def __init__(self, snapshot_path: Optional[str] = None):
        """
        Initialize schema manager.
        
        Args:
            snapshot_path: Path to store schema snapshots
        """
        self.snapshot_path: str = snapshot_path or os.path.join(
            config.DATA_DIR, "schema_snapshots"
        )
        os.makedirs(self.snapshot_path, exist_ok=True)
        self.current_snapshot: Optional[SchemaSnapshot] = None
        self.last_snapshot: Optional[SchemaSnapshot] = None
    
    def get_current_schema(self) -> SchemaSnapshot:
        """
        Get current database schema.
        
        Returns:
            Current schema snapshot
        """
        from chat_sql.db.schema_loader import schema_loader
        
        tables = []
        table_names = schema_loader.get_all_tables()
        
        for table_name in table_names:
            table_info = schema_loader.get_table_info(table_name)
            
            # Create column list
            columns = []
            for col in table_info.columns:
                columns.append({
                    'name': col.name,
                    'data_type': col.data_type,
                    'is_primary_key': col.is_primary_key,
                    'is_foreign_key': col.is_foreign_key,
                    'references_table': col.references_table,
                    'references_column': col.references_column
                })
            
            # Calculate table checksum
            table_checksum = self._calculate_table_checksum(
                table_name, columns, table_info.row_count
            )
            
            tables.append(TableSnapshot(
                name=table_name,
                columns=columns,
                row_count=table_info.row_count,
                checksum=table_checksum,
                last_updated=datetime.now()
            ))
        
        # Calculate overall schema checksum
        schema_data = {
            'tables': [
                {
                    'name': table.name,
                    'columns': table.columns,
                    'row_count': table.row_count,
                    'checksum': table.checksum,
                    'last_updated': table.last_updated.isoformat()
                }
                for table in tables
            ]
        }
        schema_checksum = hashlib.md5(json.dumps(schema_data, sort_keys=True).encode()).hexdigest()
        
        self.current_snapshot = SchemaSnapshot(
            tables=tables,
            checksum=schema_checksum,
            created_at=datetime.now()
        )
        
        return self.current_snapshot
    
    def load_last_snapshot(self) -> Optional[SchemaSnapshot]:
        """
        Load last stored schema snapshot.
        
        Returns:
            Last snapshot or None if not found
        """
        snapshot_file = os.path.join(self.snapshot_path, "latest.json")
        
        if not os.path.exists(snapshot_file):
            return None
        
        try:
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
            
            tables = []
            for table_data in data['tables']:
                tables.append(TableSnapshot(
                    name=table_data['name'],
                    columns=table_data['columns'],
                    row_count=table_data['row_count'],
                    checksum=table_data['checksum'],
                    last_updated=datetime.fromisoformat(table_data['last_updated'])
                ))
            
            return SchemaSnapshot(
                tables=tables,
                checksum=data['checksum'],
                created_at=datetime.fromisoformat(data['created_at'])
            )
        except Exception as e:
            print(f"Error loading snapshot: {e}")
            return None
    
    def save_current_snapshot(self) -> None:
        """Save current schema snapshot."""
        if not self.current_snapshot:
            return
        
        snapshot_file = os.path.join(self.snapshot_path, "latest.json")
        
        data = {
            'tables': [
                {
                    'name': table.name,
                    'columns': table.columns,
                    'row_count': table.row_count,
                    'checksum': table.checksum,
                    'last_updated': table.last_updated.isoformat()
                }
                for table in self.current_snapshot.tables
            ],
            'checksum': self.current_snapshot.checksum,
            'created_at': self.current_snapshot.created_at.isoformat()
        }
        
        with open(snapshot_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also save with timestamp for history
        timestamp_file = os.path.join(
            self.snapshot_path, 
            f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(timestamp_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def detect_changes(self) -> SchemaDiff:
        """
        Detect changes between current and last schema.
        
        Returns:
            SchemaDiff with detected changes
        """
        if not self.last_snapshot:
            # First time - all tables are new
            self.last_snapshot = self.load_last_snapshot()
            if not self.last_snapshot:
                diff = SchemaDiff()
                assert self.current_snapshot is not None, "current_snapshot must be set"
                diff.added_tables = [t.name for t in self.current_snapshot.tables]
                return diff
        
        diff = SchemaDiff()
        
        # Create lookup dictionaries
        assert self.current_snapshot is not None, "current_snapshot must be set"
        assert self.last_snapshot is not None, "last_snapshot must be set"
        current_tables = {t.name: t for t in self.current_snapshot.tables}
        last_tables = {t.name: t for t in self.last_snapshot.tables}
        
        # Find added tables
        for table_name in current_tables:
            if table_name not in last_tables:
                diff.added_tables.append(table_name)
        
        # Find removed tables
        for table_name in last_tables:
            if table_name not in current_tables:
                diff.removed_tables.append(table_name)
        
        # Find modified tables
        for table_name in current_tables:
            if table_name in last_tables:
                current_table = current_tables[table_name]
                last_table = last_tables[table_name]
                
                if current_table.checksum != last_table.checksum:
                    diff.modified_tables.append(table_name)
        
        # Find unchanged tables
        for table_name in current_tables:
            if table_name in last_tables:
                current_table = current_tables[table_name]
                last_table = last_tables[table_name]
                
                if current_table.checksum == last_table.checksum:
                    diff.unchanged_tables.append(table_name)
        
        return diff
    
    def get_tables_for_embedding(self) -> List[str]:
        """
        Get list of tables that need to be embedded.
        
        Returns:
            List of table names to embed
        """
        diff = self.detect_changes()
        
        # Only embed new or modified tables
        return diff.added_tables + diff.modified_tables
    
    def get_table_document(self, table_name: str) -> str:
        """
        Get formatted document for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Formatted table document
        """
        if not self.current_snapshot:
            self.get_current_schema()
        
        # Find table in current snapshot
        assert self.current_snapshot is not None, "current_snapshot must be set"
        for table in self.current_snapshot.tables:
            if table.name == table_name:
                doc = f"Table: {table.name}\n"
                doc += f"Description: Table with {table.row_count} rows\n"
                doc += "Columns:\n"
                
                for col in table.columns:
                    col_desc = f"- {col['name']} ({col['data_type']})"
                    
                    if col['is_primary_key']:
                        col_desc += " [PRIMARY KEY]"
                    elif col['is_foreign_key']:
                        col_desc += f" [FOREIGN KEY -> {col['references_table']}.{col['references_column']}]"
                    
                    doc += col_desc + "\n"
                
                return doc
        
        return f"Table {table_name} not found"
    
    def extract_table_keywords(self, question: str) -> List[str]:
        """
        Extract potential table names from user question.
        
        Args:
            question: User's natural language question
            
        Returns:
            List of potential table names
        """
        if not self.current_snapshot:
            self.get_current_schema()
        
        # Simple keyword extraction - can be enhanced with NLP
        question_lower = question.lower()
        potential_tables = []
        
        # Get all table names
        assert self.current_snapshot is not None, "current_snapshot must be set"
        table_names = [t.name.lower() for t in self.current_snapshot.tables]
        
        # Find exact matches
        for table_name in table_names:
            if table_name in question_lower:
                potential_tables.append(table_name)
        
        # Find partial matches (table names that appear as words)
        words = question_lower.split()
        for word in words:
            for table_name in table_names:
                if word == table_name and table_name not in potential_tables:
                    potential_tables.append(table_name)
        
        return potential_tables
    
    def _calculate_table_checksum(self, table_name: str, columns: List[Dict], row_count: int) -> str:
        """
        Calculate checksum for a table schema.
        
        Args:
            table_name: Name of the table
            columns: List of column definitions
            row_count: Number of rows in table
            
        Returns:
            MD5 checksum of table schema
        """
        # Create normalized representation
        table_data = {
            'name': table_name,
            'columns': sorted(columns, key=lambda x: x['name']),
            'row_count': row_count
        }
        
        # Calculate MD5
        data_str = json.dumps(table_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()


# Global schema manager instance
schema_manager = SchemaManager()
