#!/bin/bash

# Script to set up PostgreSQL database for OMI

echo "Setting up PostgreSQL database for OMI..."

# Check if container is running
if ! sudo docker ps | grep -q ilm_postgres_db; then
    echo "PostgreSQL container 'ilm_postgres_db' is not running!"
    exit 1
fi

# Connect as the superuser and create the database and user
echo "Creating database and user..."

sudo docker exec -i ilm_postgres_db psql -U postgres -d postgres << EOF
-- Create user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'omi_user') THEN
        CREATE ROLE omi_user LOGIN PASSWORD 'omi_password';
    END IF;
END
\$\$;

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE omi_db OWNER omi_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'omi_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE omi_db TO omi_user;

EOF

echo "Database setup completed!"
echo "Connection URL: postgresql://omi_user:omi_password@localhost:5433/omi_db"
