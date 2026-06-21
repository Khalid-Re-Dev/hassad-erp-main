# Run Alembic database migrations (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running Alembic Migrations" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and configure your database settings."
    exit 1
}

# Load environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$name" -Value $value
    }
}

Write-Host "Database: $env:DB_NAME"
Write-Host "Host: $env:DB_HOST:$env:DB_PORT"
Write-Host ""

# Check current migration status
Write-Host "Current migration status:"
alembic current
Write-Host ""

# Run migrations
Write-Host "Applying migrations..."
alembic upgrade head

Write-Host ""
Write-Host "✓ Migrations completed successfully!" -ForegroundColor Green
Write-Host ""

# Show final status
Write-Host "Final migration status:"
alembic current
