"""
Generate large-scale mock data for TalkWithDB database.
Creates realistic users, projects, and tasks for testing and training.
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Configuration
DEFAULT_NUM_USERS = 1000
DEFAULT_NUM_PROJECTS = 200
DEFAULT_NUM_TASKS = 5000

# Sample data for realistic generation
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
    "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
    "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Olivia", "Aaron", "Gloria"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
    "Long", "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell"
]

PROJECT_NAMES = [
    "Website Redesign", "Mobile App Development", "Database Migration", "API Integration",
    "Security Audit", "Cloud Infrastructure Setup", "Machine Learning Pipeline", "Data Analytics Dashboard",
    "Customer Portal", "E-commerce Platform", "Payment Gateway Integration", "User Authentication System",
    "Notification Service", "Report Generator", "Search Engine Optimization", "Content Management System",
    "Video Streaming Platform", "Chat Application", "Inventory Management", "HR Management System",
    "Financial Reporting Tool", "Marketing Automation", "Social Media Integration", "Email Campaign Manager",
    "Document Processing Pipeline", "Image Recognition Service", "Recommendation Engine", "Fraud Detection System",
    "IoT Data Collector", "Blockchain Integration", "DevOps Automation", "Kubernetes Cluster Setup",
    "Microservices Architecture", "GraphQL API", "Real-time Analytics", "A/B Testing Framework",
    "Customer Support Chatbot", "Data Warehouse", "ETL Pipeline", "Business Intelligence Dashboard",
    "Compliance Tracking System", "Audit Log Manager", "Performance Monitoring", "Load Balancer Configuration",
    "CDN Integration", "SSL Certificate Management", "Backup Automation", "Disaster Recovery Plan",
    "Network Security Enhancement", "Penetration Testing", "Code Review Automation", "CI/CD Pipeline",
    "Documentation Generator", "API Documentation Portal", "Developer SDK", "Mobile SDK Integration",
    "Third-party Integration Hub", "Webhook Management System", "Event Processing Pipeline", "Queue Management",
    "Task Scheduler", "Cron Job Manager", "Log Aggregation System", "Error Tracking Service"
]

TASK_TITLES = [
    "Implement user authentication", "Design database schema", "Create API endpoints", "Write unit tests",
    "Configure CI/CD pipeline", "Set up monitoring dashboard", "Optimize query performance", "Implement caching layer",
    "Create user documentation", "Review pull requests", "Fix security vulnerabilities", "Update dependencies",
    "Implement logging system", "Configure error handling", "Set up staging environment", "Migrate legacy data",
    "Implement search functionality", "Create data visualization charts", "Build reporting module", "Integrate third-party API",
    "Implement payment processing", "Set up email notifications", "Create admin dashboard", "Implement role-based access",
    "Build data export feature", "Create import functionality", "Implement audit logging", "Set up automated backups",
    "Configure load balancing", "Implement rate limiting", "Create API documentation", "Build webhook system",
    "Implement real-time updates", "Set up WebSocket connections", "Create mobile-responsive UI", "Implement form validation",
    "Build file upload system", "Implement image processing", "Create PDF generator", "Set up SMS notifications",
    "Implement push notifications", "Build analytics tracking", "Create A/B test framework", "Implement feature flags",
    "Set up automated testing", "Configure code coverage", "Implement SSO integration", "Build user profile page",
    "Create settings management", "Implement dark mode", "Build notification center", "Create activity feed",
    "Implement commenting system", "Build rating/review feature", "Create tagging system", "Implement filtering/sorting",
    "Build pagination system", "Implement infinite scroll", "Create drag-and-drop UI", "Build kanban board",
    "Implement calendar view", "Create Gantt chart", "Build time tracking", "Implement invoicing system",
    "Create subscription management", "Implement usage analytics", "Build team collaboration", "Create workflow automation",
    "Implement data encryption", "Set up VPN access", "Configure firewall rules", "Implement DDoS protection",
    "Build disaster recovery", "Create rollback procedures", "Implement blue-green deployment", "Set up canary releases",
    "Build service mesh", "Implement circuit breaker", "Create health checks", "Build readiness probes"
]

TASK_STATUSES = ["pending", "in_progress", "completed", "blocked", "cancelled"]


def generate_email(first_name: str, last_name: str, user_id: int) -> str:
    """Generate realistic email addresses."""
    patterns = [
        f"{first_name.lower()}.{last_name.lower()}@company.com",
        f"{first_name.lower()[0]}{last_name.lower()}@company.com",
        f"{first_name.lower()}{last_name.lower()[0]}@company.com",
        f"{first_name.lower()}_{last_name.lower()}@company.com",
        f"{last_name.lower()}.{first_name.lower()[0]}@company.com",
    ]
    return random.choice(patterns)


def generate_users(n: int = DEFAULT_NUM_USERS) -> List[Dict[str, Any]]:
    """Generate mock user data."""
    users = []
    used_emails = set()
    
    for i in range(1, n + 1):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Ensure unique email
        attempts = 0
        while attempts < 10:
            email = generate_email(first_name, last_name, i)
            if email not in used_emails:
                used_emails.add(email)
                break
            attempts += 1
        else:
            email = f"user{i}@company.com"
        
        # Random creation date within last 2 years
        days_ago = random.randint(0, 730)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        users.append({
            "id": i,
            "name": f"{first_name} {last_name}",
            "email": email,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return users


def generate_projects(n: int = DEFAULT_NUM_PROJECTS, user_ids = None) -> List[Dict[str, Any]]:
    """Generate mock project data."""
    projects = []
    used_names = set()
    
    for i in range(1, n + 1):
        # Ensure unique project name
        name = random.choice(PROJECT_NAMES)
        while name in used_names:
            name = f"{random.choice(PROJECT_NAMES)} {random.randint(1, 999)}"
        used_names.add(name)
        
        # Random description
        descriptions = [
            f"A comprehensive solution for {name.lower()}",
            f"Enterprise-grade {name.lower()} platform",
            f"Next-generation {name.lower()} system",
            f"Scalable {name.lower()} infrastructure",
            f"Modern {name.lower()} implementation",
        ]
        description = random.choice(descriptions)
        
        # Random creation date within last year
        days_ago = random.randint(0, 365)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        projects.append({
            "id": i,
            "name": name,
            "description": description,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return projects


def generate_tasks(
    n: int = DEFAULT_NUM_TASKS,
    user_ids = None,
    project_ids = None
) -> List[Dict[str, Any]]:
    """Generate mock task data."""
    if user_ids is None:
        user_ids = list(range(1, DEFAULT_NUM_USERS + 1))
    if project_ids is None:
        project_ids = list(range(1, DEFAULT_NUM_PROJECTS + 1))
    
    tasks = []
    
    for i in range(1, n + 1):
        title = random.choice(TASK_TITLES)
        status = random.choice(TASK_STATUSES)
        
        # Weighted status distribution
        weights = [0.3, 0.3, 0.25, 0.1, 0.05]  # pending, in_progress, completed, blocked, cancelled
        status = random.choices(TASK_STATUSES, weights=weights, k=1)[0]
        
        # Random assignment (80% have assignee)
        assigned_to = random.choice(user_ids) if random.random() < 0.8 else None
        
        # Random project
        project_id = random.choice(project_ids)
        
        # Random creation date within last 6 months
        days_ago = random.randint(0, 180)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        # Random due date (20% have no due date)
        if random.random() < 0.8:
            days_from_now = random.randint(1, 90)
            due_date = (datetime.now() + timedelta(days=days_from_now)).strftime("%Y-%m-%d")
        else:
            due_date = None
        
        task = {
            "id": i,
            "title": title,
            "status": status,
            "assigned_to": assigned_to,
            "project_id": project_id,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "due_date": due_date
        }
        tasks.append(task)
    
    return tasks


def generate_sql_inserts(data: Dict[str, List[Dict]], output_path = None) -> str:
    """Generate SQL INSERT statements from mock data."""
    sql_lines = []
    
    # Users
    sql_lines.append("-- Users")
    sql_lines.append("INSERT INTO users (id, name, email, created_at) VALUES")
    user_values = []
    for user in data["users"]:
        val = f"({user['id']}, '{user['name'].replace(chr(39), chr(39)+chr(39))}', '{user['email']}', '{user['created_at']}')"
        user_values.append(val)
    sql_lines.append(",\n".join(user_values) + ";")
    
    # Projects
    sql_lines.append("\n-- Projects")
    sql_lines.append("INSERT INTO projects (id, name, description, created_at) VALUES")
    project_values = []
    for project in data["projects"]:
        desc = project['description'].replace(chr(39), chr(39)+chr(39)) if project['description'] else ''
        val = f"({project['id']}, '{project['name'].replace(chr(39), chr(39)+chr(39))}', '{desc}', '{project['created_at']}')"
        project_values.append(val)
    sql_lines.append(",\n".join(project_values) + ";")
    
    # Tasks
    sql_lines.append("\n-- Tasks")
    sql_lines.append("INSERT INTO tasks (id, title, status, assigned_to, project_id, created_at, due_date) VALUES")
    task_values = []
    for task in data["tasks"]:
        assigned = str(task['assigned_to']) if task['assigned_to'] else 'NULL'
        due = f"'{task['due_date']}'" if task['due_date'] else 'NULL'
        val = f"({task['id']}, '{task['title'].replace(chr(39), chr(39)+chr(39))}', '{task['status']}', {assigned}, {task['project_id']}, '{task['created_at']}', {due})"
        task_values.append(val)
    sql_lines.append(",\n".join(task_values) + ";")
    
    sql = "\n".join(sql_lines)
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sql)
        print(f"SQL saved to: {output_path}")
    
    return sql


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate mock data for TalkWithDB')
    parser.add_argument('--users', type=int, default=DEFAULT_NUM_USERS,
                        help=f'Number of users (default: {DEFAULT_NUM_USERS})')
    parser.add_argument('--projects', type=int, default=DEFAULT_NUM_PROJECTS,
                        help=f'Number of projects (default: {DEFAULT_NUM_PROJECTS})')
    parser.add_argument('--tasks', type=int, default=DEFAULT_NUM_TASKS,
                        help=f'Number of tasks (default: {DEFAULT_NUM_TASKS})')
    parser.add_argument('--output-dir', type=str, default='./data/mock',
                        help='Output directory')
    parser.add_argument('--format', type=str, default='all',
                        choices=['json', 'sql', 'all'],
                        help='Output format')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Set seed
    random.seed(args.seed)
    
    print(f"Generating mock data:")
    print(f"  Users: {args.users}")
    print(f"  Projects: {args.projects}")
    print(f"  Tasks: {args.tasks}")
    print()
    
    # Generate data
    print("Generating users...")
    users = generate_users(args.users)
    
    print("Generating projects...")
    projects = generate_projects(args.projects)
    
    print("Generating tasks...")
    user_ids = [u['id'] for u in users]
    project_ids = [p['id'] for p in projects]
    tasks = generate_tasks(args.tasks, user_ids, project_ids)
    
    data = {
        "users": users,
        "projects": projects,
        "tasks": tasks,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "counts": {
                "users": len(users),
                "projects": len(projects),
                "tasks": len(tasks)
            }
        }
    }
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    if args.format in ['json', 'all']:
        json_path = output_dir / 'mock_data.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"JSON saved to: {json_path}")
    
    # Save SQL
    if args.format in ['sql', 'all']:
        sql_path = output_dir / 'mock_data.sql'
        generate_sql_inserts(data, sql_path)
    
    # Print statistics
    print("\n=== Data Statistics ===")
    print(f"Users: {len(users)}")
    print(f"Projects: {len(projects)}")
    print(f"Tasks: {len(tasks)}")
    
    # Task status breakdown
    status_counts = {}
    for task in tasks:
        status = task['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    print("\nTask Status Distribution:")
    for status, count in sorted(status_counts.items()):
        pct = (count / len(tasks)) * 100
        print(f"  {status}: {count} ({pct:.1f}%)")
    
    # Assignment stats
    assigned_tasks = sum(1 for t in tasks if t['assigned_to'])
    print(f"\nTasks with assignees: {assigned_tasks} ({assigned_tasks/len(tasks)*100:.1f}%)")
    
    print(f"\nDone! Data saved to: {output_dir}")


if __name__ == '__main__':
    main()
