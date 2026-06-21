#!/bin/bash
# Run Alembic database migrations

set -e

echo "=========================================="
echo "Running Alembic Migrations"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your database settings."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check current migration status
echo "Current migration status:"
alembic current
echo ""

# Run migrations
echo "Applying migrations..."
alembic upgrade head

echo ""
echo "✓ Migrations completed successfully!"
echo ""

# Show final status
echo "Final migration status:"
alembic current
