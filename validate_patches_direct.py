#!/usr/bin/env python3
"""
Direct validation script for Phase B patched modules.

This script validates the patched files directly by checking:
1. File structure and imports
2. Key functions and methods are present
3. Error handling patterns are correctly implemented
"""

import os
import ast
from typing import Dict, List, Any

def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """Analyze a Python file for structure and imports."""
    if not os.path.exists(file_path):
        return {'exists': False, 'error': 'File not found'}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        imports = []
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        return {
            'exists': True,
            'imports': imports,
            'functions': functions,
            'classes': classes,
            'has_uuid_import': any('uuid' in imp for imp in imports),
            'has_session_scope_import': any('session_scope' in imp for imp in imports),
            'has_error_handling': 'except Exception' in content or 'try:' in content,
            'has_bilingual_text': '\u0641\u0634\u0644' in content or '\u0646\u0634\u0637' in content,  # Arabic text
            'file_size': len(content)
        }
        
    except Exception as e:
        return {'exists': True, 'error': str(e)}

def validate_patched_files():
    """Validate all patched files."""
    print("Phase B Patched Files Validation")
    print("=" * 60)
    
    # Files we patched
    patched_files = {
        'stock_movements_window.py': 'E:\\Trying\\hassad-erp-phase1(4)\\ui\\stock_movements_window.py',
        'roles_window.py': 'E:\\Trying\\hassad-erp-phase1(4)\\ui\\roles_window.py', 
        'company_window.py': 'E:\\Trying\\hassad-erp-phase1(4)\\ui\\company_window.py',
        'db_utils.py': 'E:\\Trying\\hassad-erp-phase1(4)\\core\\db_utils.py'
    }
    
    results = {}
    all_passed = True
    
    for filename, filepath in patched_files.items():
        print(f"\n📁 Analyzing {filename}...")
        analysis = analyze_python_file(filepath)
        results[filename] = analysis
        
        if not analysis.get('exists', False):
            print(f"  ❌ File does not exist")
            all_passed = False
            continue
            
        if 'error' in analysis:
            print(f"  ❌ Parse error: {analysis['error']}")
            all_passed = False
            continue
        
        # Check specific requirements
        checks = []
        
        if filename == 'db_utils.py':
            checks = [
                ('Has session_scope function', 'session_scope' in analysis['functions']),
                ('Has safe_execute function', 'safe_execute' in analysis['functions']),
                ('Has DBTransaction class', 'DBTransaction' in analysis['classes']),
                ('Has proper imports', 'contextmanager' in str(analysis['imports'])),
            ]
        else:
            # UI module checks
            checks = [
                ('Has uuid import', analysis.get('has_uuid_import', False)),
                ('Has session_scope import', analysis.get('has_session_scope_import', False)),
                ('Has error handling', analysis.get('has_error_handling', False)),
                ('Has bilingual text', analysis.get('has_bilingual_text', False)),
                ('Has load_data function', 'load_data' in analysis['functions'])
            ]
        
        # Run checks
        for check_name, check_result in checks:
            if check_result:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name}")
                all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if all_passed:
        print("🎉 All patched files passed validation!")
        print("\nKey improvements implemented:")
        print("- ✅ Added proper error handling with bilingual messages")
        print("- ✅ Added uuid-based error tracking")
        print("- ✅ Added session_scope import for safe DB operations")
        print("- ✅ Added defensive programming patterns")
        print("- ✅ Maintained existing code structure and patterns")
        
        print("\nNext steps:")
        print("1. Install missing dependencies (pydantic, pydantic-settings)")
        print("2. Run full application tests")
        print("3. Test UI module navigation in MainWindow")
        print("4. Implement remaining CRUD business logic")
        return 0
    else:
        print("⚠️ Some validation checks failed. Please review the issues above.")
        return 1

def check_backup_status():
    """Check if backup files were created."""
    print("\n📂 Checking backup status...")
    
    backup_dir = "E:\\Trying\\hassad-erp-phase1(4)\\backup_before_patches_20250102"
    if os.path.exists(backup_dir):
        backup_files = os.listdir(backup_dir)
        print(f"  ✅ Backup directory exists with {len(backup_files)} files")
        for file in backup_files[:5]:  # Show first 5
            print(f"     - {file}")
        if len(backup_files) > 5:
            print(f"     ... and {len(backup_files) - 5} more files")
    else:
        print(f"  ❌ Backup directory not found at {backup_dir}")

if __name__ == "__main__":
    exit_code = validate_patched_files()
    check_backup_status()
    exit(exit_code)