#!/bin/bash
# Format and lint Python code

set -e

echo "=========================================="
echo "Formatting and Linting Code"
echo "=========================================="

echo "Running Black (code formatter)..."
black .

echo ""
echo "Running isort (import sorter)..."
isort .

echo ""
echo "Running Flake8 (linter)..."
flake8 . --max-line-length=100 --extend-ignore=E203,W503

echo ""
echo "Running mypy (type checker)..."
mypy . --ignore-missing-imports

echo ""
echo "✓ Code formatting and linting completed!"
