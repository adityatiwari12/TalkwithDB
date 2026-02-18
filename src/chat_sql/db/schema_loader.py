"""
Database schema loader for extracting table and column information.
Converts schema into text documents for RAG retrieval.
"""

import psycopg2
from typing import List, Dict, Any
from dataclasses import dataclass

from config import config
from db.connection import db_connection


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    data_type: str
    is_primary_key: bool
    is_foreign_key: bool
    references_table: str = None
    references_column: str = None


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    columns: List[ColumnInfo]
    row_count: int


class SchemaLoader:
    """Loads and formats database schema for RAG retrieval."""
    
    def __init__(self):
        """Initialize schema loader."""
        self.db = db_connection
    
    def get_table_info(self, table_name: str) -> TableInfo:
        """
        Get detailed information about a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            TableInfo object with table details
        """
        # Get column information
        columns_query = """
        SELECT 
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku
                ON tc.constraint_name = ku.constraint_name
                AND tc.table_schema = ku.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = %s
        ) pk ON c.column_name = pk.column_name
        WHERE c.table_name = %s
        ORDER BY c.ordinal_position
        """
        
        # Get foreign key information
        fk_query = """
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
        """
        
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get columns
                cursor.execute(columns_query, (table_name, table_name))
                column_rows = cursor.fetchall()
                
                # Get foreign keys
                cursor.execute(fk_query, (table_name,))
                fk_rows = cursor.fetchall()
                fk_map = {row[0]: (row[1], row[2]) for row in fk_rows}
                
                # Get row count
                cursor.execute(count_query)
                row_count = cursor.fetchone()[0]
        
        # Build column info
        columns = []
        for col_row in column_rows:
            col_name, data_type, is_nullable, col_default, is_pk = col_row
            is_fk = col_name in fk_map
            
            column = ColumnInfo(
                name=col_name,
                data_type=data_type,
                is_primary_key=is_pk,
                is_foreign_key=is_fk,
                references_table=fk_map[col_name][0] if is_fk else None,
                references_column=fk_map[col_name][1] if is_fk else None
            )
            columns.append(column)
        
        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=row_count
        )
    
    def get_all_tables(self) -> List[str]:
        """
        Get list of all user tables in the database.
        
        Returns:
            List of table names
        """
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return [row[0] for row in cursor.fetchall()]
    
    def schema_to_documents(self) -> List[str]:
        """
        Convert database schema to text documents for embedding.
        
        Returns:
            List of schema documents
        """
        documents = []
        tables = self.get_all_tables()
        
        # Create a document for each table
        for table_name in tables:
            table_info = self.get_table_info(table_name)
            
            doc = f"Table: {table_name}\n"
            doc += f"Description: Table with {table_info.row_count} rows\n"
            doc += "Columns:\n"
            
            for col in table_info.columns:
                col_desc = f"- {col.name} ({col.data_type})"
                
                if col.is_primary_key:
                    col_desc += " [PRIMARY KEY]"
                elif col.is_foreign_key:
                    col_desc += f" [FOREIGN KEY -> {col.references_table}.{col.references_column}]"
                
                doc += col_desc + "\n"
            
            documents.append(doc)
        
        # Create relationship documents
        relationship_docs = self._create_relationship_documents(tables)
        documents.extend(relationship_docs)
        
        return documents
    
    def _create_relationship_documents(self, tables: List[str]) -> List[str]:
        """
        Create documents describing table relationships.
        
        Args:
            tables: List of table names
            
        Returns:
            List of relationship documents
        """
        relationships = []
        
        for table_name in tables:
            table_info = self.get_table_info(table_name)
            
            # Find foreign key relationships
            for col in table_info.columns:
                if col.is_foreign_key:
                    rel_doc = (
                        f"Relationship: {table_name}.{col.name} "
                        f"references {col.references_table}.{col.references_column}"
                    )
                    relationships.append(rel_doc)
        
        return relationships


# Global schema loader instance
schema_loader = SchemaLoader()
