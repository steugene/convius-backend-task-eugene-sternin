-- Database initialization script for Lunch Voting API
-- This script runs when the PostgreSQL container starts for the first time

-- Create the database (if not exists)
SELECT 'CREATE DATABASE lunch_voting'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lunch_voting')\gexec

-- Connect to the lunch_voting database
\c lunch_voting;

-- Create user if not exists (PostgreSQL 15+ syntax)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'lunch_voting') THEN
        CREATE USER lunch_voting WITH PASSWORD 'secure_password';
    END IF;
END $$;

-- Grant all privileges on database to the user
GRANT ALL PRIVILEGES ON DATABASE lunch_voting TO lunch_voting;

-- Grant usage and create on schema
GRANT USAGE, CREATE ON SCHEMA public TO lunch_voting;

-- Grant all privileges on all tables (current and future)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lunch_voting;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lunch_voting;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO lunch_voting;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO lunch_voting;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO lunch_voting;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO lunch_voting;

-- Make the user the owner of the database for full access
ALTER DATABASE lunch_voting OWNER TO lunch_voting;

-- Update pg_hba.conf to allow host connections
-- This allows the lunch_voting user to connect from the host for testing
COPY (SELECT 'host lunch_voting lunch_voting 0.0.0.0/0 md5') TO PROGRAM 'echo "host lunch_voting lunch_voting 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf';

-- Reload PostgreSQL configuration to apply pg_hba.conf changes
SELECT pg_reload_conf();

-- Display success message
SELECT 'Database and user setup completed successfully!' as status;
