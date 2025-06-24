#!/bin/bash
# Script to set up PostgreSQL database for OMI, including the pgvector extension.

set -e # Exit immediately if a command exits with a non-zero status.

echo "Setting up PostgreSQL database for OMI..."

# Check if container is running
if ! sudo docker ps | grep -q ilm_postgres_db; then
    echo "PostgreSQL container 'ilm_postgres_db' is not running!"
    exit 1
fi

# 1. Connect as the superuser to the default 'postgres' database to create the new user and database.
echo "Creating database 'omi_db' and user 'omi_user'..."
sudo docker exec -i ilm_postgres_db psql -U postgres -d postgres << EOF
-- Create user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'omi_user') THEN
        CREATE ROLE omi_user LOGIN PASSWORD 'omi_password';
    END IF;
END
\$\$;

-- Create database if it doesn't exist, and set the owner
SELECT 'CREATE DATABASE omi_db OWNER omi_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'omi_db')\gexec

-- Grant privileges (This is good, but the owner already has them)
GRANT ALL PRIVILEGES ON DATABASE omi_db TO omi_user;
EOF

# 2. Connect to the newly created 'omi_db' database to enable the vector extension.
echo "Enabling 'vector' extension in database 'omi_db'..."
sudo docker exec -i ilm_postgres_db psql -U postgres -d omi_db << EOF
CREATE EXTENSION IF NOT EXISTS vector;
EOF

echo "Database setup completed successfully!"
echo "Connection URL: postgresql://omi_user:omi_password@localhost:5433/omi_db"