# TalkWithDB Database Showcase (SQL Demo Guide)

Use this file to demonstrate the **actual database** during interviews/jury review.
It is structured so you can show:

1. schema exists,
2. data is populated,
3. table relationships are real,
4. business-level insights can be derived from SQL.

---

## 1) Connect to PostgreSQL

If running via Docker:

```bash
docker exec -it talkwithdb_postgres psql -U postgres -d chatdb
```

If using local PostgreSQL client:

```bash
psql -h localhost -p 5432 -U postgres -d chatdb
```

---

## 2) Show Schema Exists

```sql
\dt
```

```sql
\d users
\d projects
\d tasks
```

What to say:

- These commands prove real relational tables exist.
- The schema includes keys and foreign-key relationships.

---

## 3) Show Data Volume

```sql
SELECT COUNT(*) AS users_count FROM users;
SELECT COUNT(*) AS projects_count FROM projects;
SELECT COUNT(*) AS tasks_count FROM tasks;
```

What to say:

- This confirms non-empty production-like sample data.

---

## 4) Show Actual Rows (Sample Data)

```sql
SELECT * FROM users LIMIT 5;
SELECT * FROM projects LIMIT 5;
SELECT * FROM tasks LIMIT 10;
```

What to say:

- These are real stored rows, not hardcoded UI output.

---

## 5) Show Table Relationships (JOIN Proof)

```sql
SELECT
  t.id,
  t.title,
  t.status,
  u.name AS assigned_user,
  p.name AS project_name
FROM tasks t
LEFT JOIN users u ON t.assigned_to = u.id
LEFT JOIN projects p ON t.project_id = p.id
ORDER BY t.id
LIMIT 10;
```

What to say:

- This proves cross-table relationships are correctly connected.

---

## 6) Business Insight Queries (Interview Strength)

### A) Project-wise completed tasks

```sql
SELECT
  p.name AS project_name,
  COUNT(t.id) AS completed_tasks
FROM projects p
JOIN tasks t ON p.id = t.project_id
WHERE t.status = 'completed'
GROUP BY p.id, p.name
ORDER BY completed_tasks DESC
LIMIT 10;
```

### B) Top users by assigned tasks

```sql
SELECT
  u.name,
  COUNT(t.id) AS task_count
FROM users u
LEFT JOIN tasks t ON u.id = t.assigned_to
GROUP BY u.id, u.name
ORDER BY task_count DESC
LIMIT 10;
```

### C) Overdue open tasks

```sql
SELECT
  t.id,
  t.title,
  t.due_date,
  t.status,
  u.name AS assigned_user
FROM tasks t
LEFT JOIN users u ON u.id = t.assigned_to
WHERE t.due_date < CURRENT_DATE
  AND t.status NOT IN ('completed', 'cancelled')
ORDER BY t.due_date ASC
LIMIT 20;
```

### D) Status distribution

```sql
SELECT
  status,
  COUNT(*) AS task_count
FROM tasks
GROUP BY status
ORDER BY task_count DESC;
```

---

## 7) Explain How This Connects to TalkWithDB

Use this short script:

> "These SQL queries run directly on the same PostgreSQL database that TalkWithDB uses.  
> The desktop assistant converts natural-language prompts into safe read-only SQL, executes against this schema, and returns explainable summaries.  
> So the AI output is grounded in actual relational data, not generated text alone."

---

## 8) Exit

```sql
\q
```

