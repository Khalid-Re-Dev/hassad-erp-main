#!/bin/bash
# Create PostgreSQL database for Hassad ERP

set -e

echo "=========================================="
echo "Creating Hassad ERP Database"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found, using defaults"
    DB_NAME="hassad_erp"
    DB_USER="hassad_user"
    DB_PASSWORD="hassad_password"
fi

echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "Error: PostgreSQL is not running!"
    echo "Please start PostgreSQL and try again."
    exit 1
fi

# Create database user if not exists
echo "Creating database user..."
psql -U postgres -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
    psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Create database if not exists
echo "Creating database..."
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Grant privileges
echo "Granting privileges..."
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo ""
echo "✓ Database created successfully!"
echo ""
echo "Connection details:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: localhost"
echo "  Port: 5432"
echo ""
echo "Next steps:"
echo "  1. Run migrations: ./scripts/run_migrations.sh"
echo "  2. Seed data: python scripts/seed_data.py"
