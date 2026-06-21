# Create PostgreSQL database for Hassad ERP (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Creating Hassad ERP Database" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Load environment variables
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
} else {
    Write-Host "Warning: .env file not found, using defaults" -ForegroundColor Yellow
    $env:DB_NAME = "hassad_erp"
    $env:DB_USER = "hassad_user"
    $env:DB_PASSWORD = "hassad_password"
}

Write-Host "Database Name: $env:DB_NAME"
Write-Host "Database User: $env:DB_USER"
Write-Host ""

# Check if PostgreSQL is running
try {
    $null = & pg_isready 2>&1
} catch {
    Write-Host "Error: PostgreSQL is not running!" -ForegroundColor Red
    Write-Host "Please start PostgreSQL and try again."
    exit 1
}

# Create database user if not exists
Write-Host "Creating database user..."
$userExists = & psql -U postgres -tc "SELECT 1 FROM pg_user WHERE usename = '$env:DB_USER'" 2>&1
if ($userExists -notmatch "1") {
    & psql -U postgres -c "CREATE USER $env:DB_USER WITH PASSWORD '$env:DB_PASSWORD';"
}

# Create database if not exists
Write-Host "Creating database..."
$dbExists = & psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$env:DB_NAME'" 2>&1
if ($dbExists -notmatch "1") {
    & psql -U postgres -c "CREATE DATABASE $env:DB_NAME OWNER $env:DB_USER;"
}

# Grant privileges
Write-Host "Granting privileges..."
& psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $env:DB_NAME TO $env:DB_USER;"

Write-Host ""
Write-Host "✓ Database created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Connection details:"
Write-Host "  Database: $env:DB_NAME"
Write-Host "  User: $env:DB_USER"
Write-Host "  Host: localhost"
Write-Host "  Port: 5432"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run migrations: .\scripts\run_migrations.ps1"
Write-Host "  2. Seed data: python scripts/seed_data.py"
