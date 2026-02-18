-- Database initialization script for Chat with SQL
-- This script is run when the PostgreSQL container starts for the first time

-- Create the sample database structure
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(50),
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    assigned_to INTEGER REFERENCES users(id),
    project_id INTEGER REFERENCES projects(id),
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    start_date DATE,
    due_date DATE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Time tracking table
CREATE TABLE IF NOT EXISTS time_entries (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id),
    user_id INTEGER REFERENCES users(id),
    hours DECIMAL(5,2) NOT NULL,
    description TEXT,
    entry_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project teams table
CREATE TABLE IF NOT EXISTS project_teams (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);

-- Insert sample data if tables are empty
DO $$
BEGIN
    -- Check if users table is empty
    IF (SELECT COUNT(*) FROM users) = 0 THEN
        INSERT INTO users (name, email, department, role) VALUES
        ('Aditya Kumar', 'aditya@example.com', 'Engineering', 'Developer'),
        ('Priya Sharma', 'priya@example.com', 'Engineering', 'Senior Developer'),
        ('Rohit Verma', 'rohit@example.com', 'Product', 'Product Manager'),
        ('Neha Patel', 'neha@example.com', 'Design', 'UX Designer'),
        ('Vikram Singh', 'vikram@example.com', 'Engineering', 'DevOps Engineer');
        
        RAISE NOTICE 'Inserted sample users';
    END IF;
    
    -- Check if projects table is empty
    IF (SELECT COUNT(*) FROM projects) = 0 THEN
        INSERT INTO projects (name, description, status, start_date, end_date, budget) VALUES
        ('Website Redesign', 'Complete redesign of company website', 'active', '2024-01-01', '2024-06-30', 50000.00),
        ('Mobile App Development', 'Native mobile app for iOS and Android', 'active', '2024-02-01', '2024-12-31', 150000.00),
        ('API Integration', 'Integration with third-party APIs', 'completed', '2023-11-01', '2024-01-31', 25000.00),
        ('Database Migration', 'Migrate legacy database to new system', 'planning', '2024-03-01', '2024-08-31', 75000.00),
        ('Security Audit', 'Comprehensive security assessment', 'active', '2024-01-15', '2024-03-15', 30000.00);
        
        RAISE NOTICE 'Inserted sample projects';
    END IF;
    
    -- Check if tasks table is empty
    IF (SELECT COUNT(*) FROM tasks) = 0 THEN
        INSERT INTO tasks (title, description, status, priority, assigned_to, project_id, estimated_hours, due_date) VALUES
        ('Design Homepage', 'Create mockups for new homepage design', 'completed', 'high', 4, 1, 40.0, '2024-01-15'),
        ('Implement User Auth', 'Add user authentication system', 'in_progress', 'high', 1, 2, 60.0, '2024-03-01'),
        ('Database Schema', 'Design database schema for mobile app', 'completed', 'medium', 2, 2, 30.0, '2024-02-15'),
        ('API Documentation', 'Document all API endpoints', 'pending', 'low', 3, 3, 20.0, '2024-02-01'),
        ('Security Testing', 'Perform security penetration testing', 'pending', 'high', 5, 5, 50.0, '2024-03-10'),
        ('UI Components', 'Create reusable UI components', 'in_progress', 'medium', 1, 1, 35.0, '2024-02-20'),
        ('Performance Optimization', 'Optimize database queries', 'completed', 'medium', 2, 4, 25.0, '2024-02-10'),
        ('Deploy to Production', 'Deploy application to production server', 'pending', 'high', 5, 1, 15.0, '2024-03-05');
        
        RAISE NOTICE 'Inserted sample tasks';
    END IF;
    
    -- Check if time_entries table is empty
    IF (SELECT COUNT(*) FROM time_entries) = 0 THEN
        INSERT INTO time_entries (task_id, user_id, hours, description, entry_date) VALUES
        (1, 4, 8.0, 'Homepage mockup design', '2024-01-10'),
        (1, 4, 6.5, 'Homepage revisions', '2024-01-12'),
        (2, 1, 7.0, 'Authentication backend', '2024-02-01'),
        (2, 1, 5.5, 'JWT token implementation', '2024-02-03'),
        (3, 2, 4.0, 'Database design review', '2024-02-05'),
        (6, 1, 6.0, 'Button component development', '2024-02-08'),
        (7, 2, 5.0, 'Query optimization', '2024-02-06'),
        (7, 2, 4.5, 'Index optimization', '2024-02-07');
        
        RAISE NOTICE 'Inserted sample time entries';
    END IF;
    
    -- Check if project_teams table is empty
    IF (SELECT COUNT(*) FROM project_teams) = 0 THEN
        INSERT INTO project_teams (project_id, user_id, role) VALUES
        (1, 1, 'member'),
        (1, 4, 'member'),
        (2, 1, 'lead'),
        (2, 2, 'member'),
        (2, 5, 'member'),
        (3, 2, 'lead'),
        (3, 3, 'member'),
        (4, 2, 'lead'),
        (4, 5, 'member'),
        (5, 5, 'lead'),
        (5, 1, 'member');
        
        RAISE NOTICE 'Inserted sample project teams';
    END IF;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_time_entries_task_id ON time_entries(task_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_user_id ON time_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_entry_date ON time_entries(entry_date);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to the chatuser
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chatuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chatuser;

-- Create view for task statistics
CREATE OR REPLACE VIEW task_statistics AS
SELECT 
    p.name as project_name,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'pending' THEN 1 END) as pending_tasks,
    ROUND(COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / COUNT(t.id), 2) as completion_percentage
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
GROUP BY p.id, p.name;

GRANT SELECT ON task_statistics TO chatuser;

-- Create view for user workload
CREATE OR REPLACE VIEW user_workload AS
SELECT 
    u.name,
    u.email,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as active_tasks,
    COALESCE(SUM(te.hours), 0) as total_hours_logged
FROM users u
LEFT JOIN tasks t ON u.id = t.assigned_to
LEFT JOIN time_entries te ON u.id = te.user_id
GROUP BY u.id, u.name, u.email;

GRANT SELECT ON user_workload TO chatuser;

RAISE NOTICE 'Database initialization completed successfully';
