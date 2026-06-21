# Format and lint Python code (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Formatting and Linting Code" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "Running Black (code formatter)..."
black .

Write-Host ""
Write-Host "Running isort (import sorter)..."
isort .

Write-Host ""
Write-Host "Running Flake8 (linter)..."
flake8 . --max-line-length=100 --extend-ignore=E203,W503

Write-Host ""
Write-Host "Running mypy (type checker)..."
mypy . --ignore-missing-imports

Write-Host ""
Write-Host "✓ Code formatting and linting completed!" -ForegroundColor Green
