"""
Generate large-scale mock data for TalkWithDB (1000+ rows per table, 10+ columns).
Includes extended schema with departments, comments, task_history, tags.
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Large-scale configuration
DEFAULT_NUM_DEPARTMENTS = 20
DEFAULT_NUM_USERS = 2000
DEFAULT_NUM_PROJECTS = 500
DEFAULT_NUM_TASKS = 10000
DEFAULT_NUM_COMMENTS = 5000
DEFAULT_NUM_TASK_HISTORY = 8000
DEFAULT_NUM_TAGS = 50

# Extended sample data
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker"
]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", 
    "Product", "Design", "Customer Support", "Legal", "IT", "Research",
    "Business Development", "Quality Assurance", "DevOps", "Data Science",
    "Security", "Compliance", "Administration", "Customer Success"
]

PROJECT_NAMES = [
    "Website Redesign", "Mobile App Development", "Database Migration", "API Integration",
    "Security Audit", "Cloud Infrastructure", "ML Pipeline", "Analytics Dashboard",
    "Customer Portal", "E-commerce Platform", "Payment Integration", "Auth System",
    "Notification Service", "Report Generator", "SEO Optimization", "CMS",
    "Video Platform", "Chat App", "Inventory System", "HR System",
    "Financial Tool", "Marketing Automation", "Social Integration", "Email Manager",
    "Document Pipeline", "Image Recognition", "Recommendation Engine", "Fraud Detection",
    "IoT Collector", "Blockchain", "DevOps", "Kubernetes Setup",
    "Microservices", "GraphQL API", "Real-time Analytics", "A/B Testing",
    "Support Chatbot", "Data Warehouse", "ETL Pipeline", "BI Dashboard",
    "Compliance Tracker", "Audit Manager", "Performance Monitor", "Load Balancer",
    "CDN Integration", "SSL Management", "Backup System", "Disaster Recovery",
    "Network Security", "Penetration Testing", "Code Review", "CI/CD",
    "Documentation", "API Portal", "Developer SDK", "Mobile SDK",
    "Integration Hub", "Webhook Manager", "Event Pipeline", "Queue System"
]

TASK_TITLES = [
    "Implement user authentication", "Design database schema", "Create API endpoints", "Write unit tests",
    "Configure CI/CD", "Setup monitoring", "Optimize queries", "Implement caching",
    "Create documentation", "Review PRs", "Fix vulnerabilities", "Update dependencies",
    "Implement logging", "Configure error handling", "Setup staging", "Migrate data",
    "Implement search", "Create visualizations", "Build reporting", "Integrate API",
    "Implement payments", "Setup notifications", "Create admin dashboard", "Implement RBAC",
    "Build export feature", "Create import", "Implement audit log", "Setup backups",
    "Configure load balancing", "Implement rate limiting", "Create API docs", "Build webhooks",
    "Implement real-time", "Setup WebSocket", "Create responsive UI", "Implement validation",
    "Build file upload", "Implement image processing", "Create PDF generator", "Setup SMS",
    "Implement push notifications", "Build analytics", "Create A/B tests", "Feature flags",
    "Setup automated tests", "Configure coverage", "Implement SSO", "Build profile page",
    "Create settings", "Implement dark mode", "Build notifications", "Activity feed",
    "Implement comments", "Build rating system", "Create tagging", "Filter/sort",
    "Build pagination", "Infinite scroll", "Drag-and-drop", "Kanban board",
    "Calendar view", "Gantt chart", "Time tracking", "Invoicing",
    "Subscription management", "Usage analytics", "Team collaboration", "Workflow automation"
]

TASK_STATUSES = ["pending", "in_progress", "completed", "blocked", "cancelled"]

COMMENT_TEMPLATES = [
    "Working on this now. Should be done by {date}.",
    "Need more clarification on requirements.",
    "This is blocked by another task.",
    "Completed and tested.",
    "Found a bug, investigating.",
    "Ready for review.",
    "Deployed to staging.",
    "Updated the documentation.",
    "Need help with this one.",
    "Reassigning to {name}.",
    "Merged to main branch.",
    "Waiting for approval.",
    "Fixed the issue.",
    "Added tests for edge cases.",
    "Performance looks good."
]

TAG_NAMES = [
    "urgent", "high-priority", "low-priority", "bug", "feature", "enhancement",
    "documentation", "testing", "frontend", "backend", "database", "api",
    "security", "performance", "refactor", "design", "mobile", "web",
    "critical", "debt", "research", "spike", "epic", "story",
    "hotfix", "release", "milestone", "customer-request", "internal",
    "blocked", "help-wanted", "good-first-issue", "dependencies", "ui", "ux",
    "accessibility", "seo", "analytics", "monitoring", "deployment",
    "data-migration", "integration", "third-party", "authentication", "authorization"
]


def generate_departments(n=DEFAULT_NUM_DEPARTMENTS) -> List[Dict]:
    """Generate department data."""
    departments = []
    for i in range(1, n + 1):
        departments.append({
            "id": i,
            "name": DEPARTMENTS[i - 1] if i <= len(DEPARTMENTS) else f"Department {i}",
            "description": f"Responsible for {DEPARTMENTS[i-1].lower()} operations" if i <= len(DEPARTMENTS) else f"Department {i} operations",
            "budget": round(random.uniform(50000, 500000), 2),
            "location": random.choice(["Floor 1", "Floor 2", "Floor 3", "Remote", "HQ"]),
            "created_at": (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime("%Y-%m-%d %H:%M:%S")
        })
    return departments


def generate_users(n=DEFAULT_NUM_USERS, dept_ids=None) -> List[Dict]:
    """Generate user data."""
    if dept_ids is None:
        dept_ids = list(range(1, DEFAULT_NUM_DEPARTMENTS + 1))
    
    users = []
    used_emails = set()
    roles = ["developer", "manager", "analyst", "designer", "admin", "tester", "devops"]
    
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        
        attempts = 0
        while attempts < 10:
            email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@company.com"
            if email not in used_emails:
                used_emails.add(email)
                break
            attempts += 1
        
        users.append({
            "id": i,
            "name": f"{first} {last}",
            "email": email,
            "role": random.choice(roles),
            "department_id": random.choice(dept_ids),
            "salary": round(random.uniform(50000, 150000), 2),
            "is_active": random.random() < 0.95,
            "hire_date": (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime("%Y-%m-%d"),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return users


def generate_projects(n=DEFAULT_NUM_PROJECTS, dept_ids=None) -> List[Dict]:
    """Generate project data."""
    if dept_ids is None:
        dept_ids = list(range(1, DEFAULT_NUM_DEPARTMENTS + 1))
    
    projects = []
    used_names = set()
    statuses = ["active", "completed", "on_hold", "cancelled"]
    priorities = ["low", "medium", "high", "critical"]
    
    for i in range(1, n + 1):
        name = random.choice(PROJECT_NAMES)
        while name in used_names:
            name = f"{random.choice(PROJECT_NAMES)} {random.randint(1, 999)}"
        used_names.add(name)
        
        start_date = datetime.now() - timedelta(days=random.randint(0, 365))
        end_date = start_date + timedelta(days=random.randint(30, 365)) if random.random() < 0.7 else None
        
        projects.append({
            "id": i,
            "name": name,
            "description": f"Enterprise {name.lower()} platform implementation",
            "status": random.choice(statuses),
            "priority": random.choice(priorities),
            "department_id": random.choice(dept_ids),
            "budget": round(random.uniform(10000, 500000), 2),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return projects


def generate_tasks(n=DEFAULT_NUM_TASKS, user_ids=None, project_ids=None) -> List[Dict]:
    """Generate task data."""
    if user_ids is None:
        user_ids = list(range(1, DEFAULT_NUM_USERS + 1))
    if project_ids is None:
        project_ids = list(range(1, DEFAULT_NUM_PROJECTS + 1))
    
    tasks = []
    types = ["feature", "bug", "task", "epic", "story"]
    priorities = ["low", "medium", "high", "urgent"]
    
    for i in range(1, n + 1):
        created = datetime.now() - timedelta(days=random.randint(0, 180))
        due = created + timedelta(days=random.randint(1, 90)) if random.random() < 0.8 else None
        
        tasks.append({
            "id": i,
            "title": random.choice(TASK_TITLES),
            "description": f"Detailed description for task {i}. This involves {random.choice(['coding', 'testing', 'documentation', 'research'])}.",
            "type": random.choice(types),
            "status": random.choices(TASK_STATUSES, weights=[0.25, 0.30, 0.30, 0.10, 0.05])[0],
            "priority": random.choice(priorities),
            "assigned_to": random.choice(user_ids) if random.random() < 0.85 else None,
            "project_id": random.choice(project_ids),
            "estimated_hours": random.randint(1, 40),
            "actual_hours": random.randint(0, 50) if random.random() < 0.6 else None,
            "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
            "due_date": due.strftime("%Y-%m-%d") if due else None,
            "completed_at": (created + timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d %H:%M:%S") if random.random() < 0.3 else None
        })
    return tasks


def generate_comments(n=DEFAULT_NUM_COMMENTS, user_ids=None, task_ids=None) -> List[Dict]:
    """Generate task comments."""
    if user_ids is None:
        user_ids = list(range(1, DEFAULT_NUM_USERS + 1))
    if task_ids is None:
        task_ids = list(range(1, DEFAULT_NUM_TASKS + 1))
    
    comments = []
    for i in range(1, n + 1):
        template = random.choice(COMMENT_TEMPLATES)
        text = template.format(
            date=(datetime.now() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            name=random.choice(["Alice", "Bob", "Charlie", "Diana"])
        )
        
        comments.append({
            "id": i,
            "task_id": random.choice(task_ids),
            "user_id": random.choice(user_ids),
            "content": text,
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d %H:%M:%S"),
            "is_edited": random.random() < 0.1
        })
    return comments


def generate_task_history(n=DEFAULT_NUM_TASK_HISTORY, task_ids=None, user_ids=None) -> List[Dict]:
    """Generate task status change history."""
    if task_ids is None:
        task_ids = list(range(1, DEFAULT_NUM_TASKS + 1))
    if user_ids is None:
        user_ids = list(range(1, DEFAULT_NUM_USERS + 1))
    
    history = []
    for i in range(1, n + 1):
        old_status = random.choice(TASK_STATUSES)
        new_status = random.choice([s for s in TASK_STATUSES if s != old_status])
        
        history.append({
            "id": i,
            "task_id": random.choice(task_ids),
            "changed_by": random.choice(user_ids),
            "field_name": random.choice(["status", "priority", "assigned_to"]),
            "old_value": old_status,
            "new_value": new_status,
            "changed_at": (datetime.now() - timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M:%S"),
            "reason": random.choice(["Progress update", "Reassignment", "Status review", "Blocker resolved", "Priority change"])
        })
    return history


def generate_tags(n=DEFAULT_NUM_TAGS) -> List[Dict]:
    """Generate tag data."""
    tags = []
    colors = ["red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan", "gray", "black"]
    
    for i in range(1, min(n + 1, len(TAG_NAMES) + 1)):
        tags.append({
            "id": i,
            "name": TAG_NAMES[i - 1],
            "color": random.choice(colors),
            "description": f"Tag for {TAG_NAMES[i-1]} items",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return tags


def generate_task_tags(task_ids=None, tag_ids=None) -> List[Dict]:
    """Generate task-tag associations."""
    if task_ids is None:
        task_ids = list(range(1, DEFAULT_NUM_TASKS + 1))
    if tag_ids is None:
        tag_ids = list(range(1, DEFAULT_NUM_TAGS + 1))
    
    associations = []
    used_pairs = set()
    
    for task_id in task_ids:
        num_tags = random.randint(0, 5)
        for _ in range(num_tags):
            tag_id = random.choice(tag_ids)
            pair = (task_id, tag_id)
            if pair not in used_pairs:
                used_pairs.add(pair)
                associations.append({
                    "task_id": task_id,
                    "tag_id": tag_id,
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
    
    return associations


def generate_sql_inserts(data: Dict, output_path=None) -> str:
    """Generate SQL INSERT statements."""
    sql_lines = ["BEGIN;", ""]
    
    # Departments (10 columns)
    sql_lines.append("-- Departments")
    sql_lines.append("INSERT INTO departments (id, name, description, budget, location, created_at) VALUES")
    values = [f"({d['id']}, '{d['name']}', '{d['description']}', {d['budget']}, '{d['location']}', '{d['created_at']}')" for d in data["departments"]]
    sql_lines.append(",\n".join(values) + ";")
    
    # Users (10 columns)
    sql_lines.append("\n-- Users")
    sql_lines.append("INSERT INTO users (id, name, email, role, department_id, salary, is_active, hire_date, created_at) VALUES")
    values = []
    for u in data["users"]:
        val = f"({u['id']}, '{u['name'].replace(chr(39), chr(39)+chr(39))}', '{u['email']}', '{u['role']}', {u['department_id']}, {u['salary']}, {u['is_active']}, '{u['hire_date']}', '{u['created_at']}')"
        values.append(val)
    sql_lines.append(",\n".join(values) + ";")
    
    # Projects (10 columns)
    sql_lines.append("\n-- Projects")
    sql_lines.append("INSERT INTO projects (id, name, description, status, priority, department_id, budget, start_date, end_date, created_at) VALUES")
    values = []
    for p in data["projects"]:
        end = f"'{p['end_date']}'" if p['end_date'] else "NULL"
        val = f"({p['id']}, '{p['name'].replace(chr(39), chr(39)+chr(39))}', '{p['description'].replace(chr(39), chr(39)+chr(39))}', '{p['status']}', '{p['priority']}', {p['department_id']}, {p['budget']}, '{p['start_date']}', {end}, '{p['created_at']}')"
        values.append(val)
    sql_lines.append(",\n".join(values) + ";")
    
    # Tasks (13 columns)
    sql_lines.append("\n-- Tasks")
    sql_lines.append("INSERT INTO tasks (id, title, description, type, status, priority, assigned_to, project_id, estimated_hours, actual_hours, created_at, due_date, completed_at) VALUES")
    values = []
    for t in data["tasks"]:
        assigned = str(t['assigned_to']) if t['assigned_to'] else 'NULL'
        due = f"'{t['due_date']}'" if t['due_date'] else 'NULL'
        completed = f"'{t['completed_at']}'" if t['completed_at'] else 'NULL'
        actual = str(t['actual_hours']) if t['actual_hours'] else 'NULL'
        val = f"({t['id']}, '{t['title'].replace(chr(39), chr(39)+chr(39))}', '{t['description'].replace(chr(39), chr(39)+chr(39))}', '{t['type']}', '{t['status']}', '{t['priority']}', {assigned}, {t['project_id']}, {t['estimated_hours']}, {actual}, '{t['created_at']}', {due}, {completed})"
        values.append(val)
    sql_lines.append(",\n".join(values) + ";")
    
    # Comments (6 columns)
    sql_lines.append("\n-- Comments")
    sql_lines.append("INSERT INTO comments (id, task_id, user_id, content, created_at, is_edited) VALUES")
    values = [f"({c['id']}, {c['task_id']}, {c['user_id']}, '{c['content'].replace(chr(39), chr(39)+chr(39))}', '{c['created_at']}', {c['is_edited']})" for c in data["comments"]]
    sql_lines.append(",\n".join(values) + ";")
    
    # Task History (8 columns)
    sql_lines.append("\n-- Task History")
    sql_lines.append("INSERT INTO task_history (id, task_id, changed_by, field_name, old_value, new_value, changed_at, reason) VALUES")
    values = [f"({h['id']}, {h['task_id']}, {h['changed_by']}, '{h['field_name']}', '{h['old_value']}', '{h['new_value']}', '{h['changed_at']}', '{h['reason']}')" for h in data["task_history"]]
    sql_lines.append(",\n".join(values) + ";")
    
    # Tags (5 columns)
    sql_lines.append("\n-- Tags")
    sql_lines.append("INSERT INTO tags (id, name, color, description, created_at) VALUES")
    values = [f"({t['id']}, '{t['name']}', '{t['color']}', '{t['description']}', '{t['created_at']}')" for t in data["tags"]]
    sql_lines.append(",\n".join(values) + ";")
    
    # Task Tags (junction table)
    sql_lines.append("\n-- Task Tags")
    sql_lines.append("INSERT INTO task_tags (task_id, tag_id, added_at) VALUES")
    values = [f"({tt['task_id']}, {tt['tag_id']}, '{tt['added_at']}')" for tt in data["task_tags"]]
    sql_lines.append(",\n".join(values) + ";")
    
    sql_lines.append("\nCOMMIT;")
    
    sql = "\n".join(sql_lines)
    
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sql)
        print(f"SQL saved to: {output_path}")
    
    return sql


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate large-scale mock data')
    parser.add_argument('--departments', type=int, default=DEFAULT_NUM_DEPARTMENTS)
    parser.add_argument('--users', type=int, default=DEFAULT_NUM_USERS)
    parser.add_argument('--projects', type=int, default=DEFAULT_NUM_PROJECTS)
    parser.add_argument('--tasks', type=int, default=DEFAULT_NUM_TASKS)
    parser.add_argument('--comments', type=int, default=DEFAULT_NUM_COMMENTS)
    parser.add_argument('--history', type=int, default=DEFAULT_NUM_TASK_HISTORY)
    parser.add_argument('--tags', type=int, default=DEFAULT_NUM_TAGS)
    parser.add_argument('--output-dir', type=str, default='./data/mock')
    parser.add_argument('--seed', type=int, default=42)
    
    args = parser.parse_args()
    random.seed(args.seed)
    
    print(f"Generating large-scale mock data:")
    print(f"  Departments: {args.departments}")
    print(f"  Users: {args.users}")
    print(f"  Projects: {args.projects}")
    print(f"  Tasks: {args.tasks}")
    print(f"  Comments: {args.comments}")
    print(f"  Task History: {args.history}")
    print(f"  Tags: {args.tags}")
    print()
    
    # Generate all data
    print("Generating departments...")
    departments = generate_departments(args.departments)
    dept_ids = [d['id'] for d in departments]
    
    print("Generating users...")
    users = generate_users(args.users, dept_ids)
    user_ids = [u['id'] for u in users]
    
    print("Generating projects...")
    projects = generate_projects(args.projects, dept_ids)
    project_ids = [p['id'] for p in projects]
    
    print("Generating tasks...")
    tasks = generate_tasks(args.tasks, user_ids, project_ids)
    task_ids = [t['id'] for t in tasks]
    
    print("Generating comments...")
    comments = generate_comments(args.comments, user_ids, task_ids)
    
    print("Generating task history...")
    history = generate_task_history(args.history, task_ids, user_ids)
    
    print("Generating tags...")
    tags = generate_tags(args.tags)
    tag_ids = [t['id'] for t in tags]
    
    print("Generating task-tag associations...")
    task_tags = generate_task_tags(task_ids, tag_ids)
    
    data = {
        "departments": departments,
        "users": users,
        "projects": projects,
        "tasks": tasks,
        "comments": comments,
        "task_history": history,
        "tags": tags,
        "task_tags": task_tags,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_rows": len(departments) + len(users) + len(projects) + len(tasks) + len(comments) + len(history) + len(tags) + len(task_tags)
        }
    }
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_dir / 'large_mock_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved to: {json_path}")
    
    # Save SQL
    sql_path = output_dir / 'large_mock_data.sql'
    generate_sql_inserts(data, sql_path)
    
    # Statistics
    print("\n=== Data Statistics ===")
    print(f"Departments: {len(departments)}")
    print(f"Users: {len(users)}")
    print(f"Projects: {len(projects)}")
    print(f"Tasks: {len(tasks)}")
    print(f"Comments: {len(comments)}")
    print(f"Task History: {len(history)}")
    print(f"Tags: {len(tags)}")
    print(f"Task-Tag Associations: {len(task_tags)}")
    print(f"TOTAL ROWS: {data['metadata']['total_rows']}")
    print(f"\nAll data saved to: {output_dir}")


if __name__ == '__main__':
    main()
