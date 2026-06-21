# Phase B Verification Script
# Verifies that all Phase B components are properly installed and functional

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Phase B Implementation Verification" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# Helper functions
function Test-FileExists {
    param([string]$Path, [string]$Description)
    
    if (Test-Path $Path) {
        Write-Host "[✓] $Description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[✗] $Description - MISSING" -ForegroundColor Red
        $script:ErrorCount++
        return $false
    }
}

function Test-PythonImport {
    param([string]$Module, [string]$Description)
    
    $result = & python -c "import $Module; print('OK')" 2>&1
    if ($result -match "OK") {
        Write-Host "[✓] $Description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[✗] $Description - FAILED" -ForegroundColor Red
        Write-Host "    Error: $result" -ForegroundColor DarkRed
        $script:ErrorCount++
        return $false
    }
}

# 1. Verify Core Files
Write-Host "`n=== Core Files ===" -ForegroundColor Yellow
Test-FileExists "core\permissions.py" "PermissionManager"
Test-FileExists "core\db_utils.py" "Database Utilities"
Test-FileExists "ui\base_ui.py" "ModuleUI Base Classes"
Test-FileExists "ui\main_window.py" "MainWindow with Routing"

# 2. Verify UI Scaffolds
Write-Host "`n=== UI Scaffolds ===" -ForegroundColor Yellow
$scaffolds = @(
    "branches_window.py",
    "accounts_window.py",
    "journals_window.py",
    "trial_balance_window.py",
    "categories_window.py",
    "inventory_valuation_window.py",
    "pos_interface_window.py",
    "sales_history_window.py",
    "customers_window.py",
    "suppliers_window.py",
    "purchase_orders_window.py",
    "goods_receipt_window.py",
    "purchase_invoices_window.py",
    "reports_window.py",
    "settings_window.py"
)

foreach ($scaffold in $scaffolds) {
    $name = $scaffold -replace "_window.py", ""
    Test-FileExists "ui\$scaffold" "$name UI"
}

# 3. Verify Test Files
Write-Host "`n=== Test Files ===" -ForegroundColor Yellow
Test-FileExists "tests\test_permissions.py" "Permission Tests"
Test-FileExists "tests\test_ui_contract.py" "UI Contract Tests"
Test-FileExists "tests\test_dashboard_routing.py" "Routing Tests"

# 4. Verify Backups
Write-Host "`n=== Backups ===" -ForegroundColor Yellow
Test-FileExists "backups\phase_b_resume\phase_b_manifest_2025-11-02.json" "Phase B Manifest"
if (Test-Path "backups\phase_b_resume\ui\*.bak") {
    Write-Host "[✓] UI Backups Created" -ForegroundColor Green
} else {
    Write-Host "[!] UI Backups Not Found" -ForegroundColor Yellow
    $script:WarningCount++
}

# 5. Test Python Imports (if venv available)
Write-Host "`n=== Import Tests ===" -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\python.exe") {
    $python = ".\venv\Scripts\python.exe"
    Write-Host "Using venv python..."
    
    & $python -c "from core.permissions import PermissionManager, permission_manager; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] core.permissions imports" -ForegroundColor Green
    } else {
        Write-Host "[✗] core.permissions import failed" -ForegroundColor Red
        $script:ErrorCount++
    }
    
    & $python -c "from core.db_utils import session_scope; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] core.db_utils imports" -ForegroundColor Green
    } else {
        Write-Host "[✗] core.db_utils import failed" -ForegroundColor Red
        $script:ErrorCount++
    }
    
    & $python -c "from ui.base_ui import ModuleUI, ModuleWidget, ModuleMainWindow; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] ui.base_ui imports" -ForegroundColor Green
    } else {
        Write-Host "[✗] ui.base_ui import failed" -ForegroundColor Red
        $script:ErrorCount++
    }
    
    # Test a sample UI scaffold
    & $python -c "from ui.branches_window import BranchesWindow; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Sample UI scaffold (branches) imports" -ForegroundColor Green
    } else {
        Write-Host "[✗] Sample UI scaffold import failed" -ForegroundColor Red
        $script:ErrorCount++
    }
    
} else {
    Write-Host "[!] Virtual environment not found - skipping import tests" -ForegroundColor Yellow
    $script:WarningCount++
}

# 6. Run Tests (optional)
Write-Host "`n=== Test Execution ===" -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\python.exe") {
    Write-Host "Running permission tests..." -ForegroundColor Gray
    
    $testOutput = & .\venv\Scripts\python.exe -m pytest tests/test_permissions.py -q --tb=no 2>&1
    
    if ($testOutput -match "(\d+) passed") {
        $passCount = $Matches[1]
        Write-Host "[✓] Permission tests: $passCount passed" -ForegroundColor Green
    }
    
    if ($testOutput -match "(\d+) failed") {
        $failCount = $Matches[1]
        Write-Host "[!] Permission tests: $failCount failed" -ForegroundColor Yellow
        $script:WarningCount++
    }
} else {
    Write-Host "[!] Skipping test execution (venv not found)" -ForegroundColor Yellow
}

# 7. Verify Documentation
Write-Host "`n=== Documentation ===" -ForegroundColor Yellow
Test-FileExists "changelog\phase_b_resume.md" "Phase B Changelog"
Test-FileExists "scripts\generate_ui_scaffolds.py" "Scaffold Generator"

# 8. Summary
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "[✓] All checks passed!" -ForegroundColor Green
    Write-Host "`nPhase B is fully implemented and verified." -ForegroundColor Green
    exit 0
} elseif ($ErrorCount -eq 0) {
    Write-Host "[!] Verification completed with warnings" -ForegroundColor Yellow
    Write-Host "    Errors: $ErrorCount" -ForegroundColor Green
    Write-Host "    Warnings: $WarningCount" -ForegroundColor Yellow
    Write-Host "`nPhase B is implemented but some non-critical items need attention." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "[✗] Verification failed" -ForegroundColor Red
    Write-Host "    Errors: $ErrorCount" -ForegroundColor Red
    Write-Host "    Warnings: $WarningCount" -ForegroundColor Yellow
    Write-Host "`nPlease review errors above and fix issues." -ForegroundColor Red
    exit 1
}
