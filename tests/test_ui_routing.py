"""
UI Routing Validation Tests.

Tests the main window routing system and module loading functionality.
"""

import sys
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Create QApplication before importing UI modules
from PyQt6.QtWidgets import QApplication
if not QApplication.instance():
    app = QApplication(sys.argv)

from ui.main_window import MODULE_REGISTRY
from core.database import SessionLocal
from core.permissions import permission_manager
from models import User


class UIRoutingValidator:
    """Validates UI routing and module loading."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.session_factory = SessionLocal
        
    def validate_all_modules(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Validate all modules in MODULE_REGISTRY.
        
        Returns:
            Tuple of (working_modules, failed_imports, failed_classes)
        """
        working_modules = []
        failed_imports = []
        failed_classes = []
        
        print("🔍 Validating UI Module Registry...")
        print(f"Total modules to test: {len(MODULE_REGISTRY)}")
        print("-" * 60)
        
        for module_id, (module_path, class_name, permission) in MODULE_REGISTRY.items():
            print(f"Testing {module_id}: {module_path}.{class_name}")
            
            try:
                # Test import
                module = importlib.import_module(module_path)
                print(f"  ✅ Import successful: {module_path}")
                
                # Test class existence
                if hasattr(module, class_name):
                    widget_class = getattr(module, class_name)
                    print(f"  ✅ Class found: {class_name}")
                    
                    # Test class instantiation (without parent for testing)
                    try:
                        # Create mock app context
                        app_context = {
                            'session_factory': self.session_factory,
                            'current_user': None,
                            'current_company': None,
                            'current_branch': None,
                            'permission_manager': permission_manager
                        }
                        
                        # Try to instantiate
                        instance = widget_class(app_context=app_context)
                        print(f"  ✅ Instantiation successful: {class_name}")
                        working_modules.append(module_id)
                        
                        # Store result
                        self.results.append({
                            'module_id': module_id,
                            'module_path': module_path,
                            'class_name': class_name,
                            'permission': permission,
                            'status': 'SUCCESS',
                            'error': None
                        })
                        
                    except Exception as e:
                        print(f"  ❌ Instantiation failed: {str(e)}")
                        failed_classes.append(f"{module_id}: {str(e)}")
                        self.results.append({
                            'module_id': module_id,
                            'module_path': module_path,
                            'class_name': class_name,
                            'permission': permission,
                            'status': 'INSTANTIATION_ERROR',
                            'error': str(e)
                        })
                else:
                    print(f"  ❌ Class not found: {class_name}")
                    failed_classes.append(f"{module_id}: Class {class_name} not found")
                    self.results.append({
                        'module_id': module_id,
                        'module_path': module_path,
                        'class_name': class_name,
                        'permission': permission,
                        'status': 'CLASS_NOT_FOUND',
                        'error': f"Class {class_name} not found in {module_path}"
                    })
                    
            except ImportError as e:
                print(f"  ❌ Import failed: {str(e)}")
                failed_imports.append(f"{module_id}: {str(e)}")
                self.results.append({
                    'module_id': module_id,
                    'module_path': module_path,
                    'class_name': class_name,
                    'permission': permission,
                    'status': 'IMPORT_ERROR',
                    'error': str(e)
                })
            
            print("-" * 40)
        
        return working_modules, failed_imports, failed_classes
    
    def generate_report(self) -> str:
        """Generate validation report."""
        working = [r for r in self.results if r['status'] == 'SUCCESS']
        import_errors = [r for r in self.results if r['status'] == 'IMPORT_ERROR']
        class_errors = [r for r in self.results if r['status'] == 'CLASS_NOT_FOUND']
        instantiation_errors = [r for r in self.results if r['status'] == 'INSTANTIATION_ERROR']
        
        report = f"""# UI Routing Validation Report

## Summary
- **Total Modules**: {len(self.results)}
- **Working Modules**: {len(working)}
- **Import Errors**: {len(import_errors)}
- **Class Not Found Errors**: {len(class_errors)}
- **Instantiation Errors**: {len(instantiation_errors)}

## Working Modules ✅
"""
        
        for result in working:
            report += f"- **{result['module_id']}**: `{result['module_path']}.{result['class_name']}`\n"
        
        if import_errors:
            report += "\n## Import Errors ❌\n"
            for result in import_errors:
                report += f"- **{result['module_id']}**: `{result['module_path']}.{result['class_name']}`\n"
                report += f"  - Error: {result['error']}\n"
        
        if class_errors:
            report += "\n## Class Not Found Errors ⚠️\n"
            for result in class_errors:
                report += f"- **{result['module_id']}**: `{result['module_path']}.{result['class_name']}`\n"
                report += f"  - Error: {result['error']}\n"
        
        if instantiation_errors:
            report += "\n## Instantiation Errors ⚠️\n"
            for result in instantiation_errors:
                report += f"- **{result['module_id']}**: `{result['module_path']}.{result['class_name']}`\n"
                report += f"  - Error: {result['error']}\n"
        
        report += f"\n## Module Registry Structure\n"
        for module_id, (module_path, class_name, permission) in MODULE_REGISTRY.items():
            report += f"- `{module_id}` → `{module_path}.{class_name}` (Requires: {permission})\n"
        
        return report


def main():
    """Run module validation."""
    validator = UIRoutingValidator()
    
    print("🚀 Starting UI Module Validation...")
    working, failed_imports, failed_classes = validator.validate_all_modules()
    
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    print(f"✅ Working modules: {len(working)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    print(f"⚠️  Failed classes: {len(failed_classes)}")
    
    if working:
        print(f"\n✅ Working modules: {', '.join(working)}")
    
    if failed_imports:
        print(f"\n❌ Import failures:")
        for failure in failed_imports:
            print(f"   - {failure}")
    
    if failed_classes:
        print(f"\n⚠️  Class failures:")
        for failure in failed_classes:
            print(f"   - {failure}")
    
    # Generate report
    report = validator.generate_report()
    
    # Write report to file
    with open('docs/UI_ROUTING_VALIDATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: docs/UI_ROUTING_VALIDATION_REPORT.md")
    
    return len(working), len(failed_imports), len(failed_classes)


if __name__ == "__main__":
    main()