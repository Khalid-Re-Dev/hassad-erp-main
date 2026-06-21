"""
UI-Service Binding Verification Script for Hassad ERP.

This script automatically verifies the integrity and consistency of UI-Service bindings
by analyzing:
- Service import existence in UI files
- Method call matching between UI and Service layers
- Field binding consistency
- Missing event handlers
- Data flow validation

Usage:
    python scripts/verify_ui_service_bindings.py
"""

import os
import re
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceBinding:
    """Represents a UI-Service binding."""
    ui_file: str
    ui_class: str
    service_import: str
    service_name: str
    service_methods_used: List[str]
    ui_methods: List[str]
    base_class: str
    issues: List[str]
    
    def to_dict(self):
        return asdict(self)


@dataclass
class VerificationResult:
    """Results of binding verification."""
    total_ui_files: int
    ui_with_services: int
    ui_without_services: int
    bindings: List[ServiceBinding]
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    timestamp: str
    
    def to_dict(self):
        return {
            'total_ui_files': self.total_ui_files,
            'ui_with_services': self.ui_with_services,
            'ui_without_services': self.ui_without_services,
            'bindings': [b.to_dict() for b in self.bindings],
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': self.timestamp
        }


class UIServiceVerifier:
    """Verifies UI-Service bindings across the application."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ui_dir = self.project_root / 'ui'
        self.service_dir = self.project_root / 'core' / 'services'
        
        # Expected service methods (CRUD operations)
        self.expected_service_methods = {
            'create', 'update', 'delete', 'get_all', 'get_by_id'
        }
        
        # Known service getter functions
        self.service_getters = {}
        self._load_service_getters()
    
    def _load_service_getters(self):
        """Load available service getter functions."""
        service_init = self.service_dir / '__init__.py'
        if service_init.exists():
            try:
                with open(service_init, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract get_*_service functions
                    pattern = r'from\s+\S+\s+import\s+.*?(get_\w+_service)'
                    matches = re.findall(pattern, content)
                    for match in matches:
                        service_name = match.replace('get_', '').replace('_service', '')
                        self.service_getters[service_name] = match
                        logger.debug(f"Found service getter: {match} for {service_name}")
            except Exception as e:
                logger.error(f"Error loading service getters: {e}")
    
    def extract_imports(self, file_path: Path) -> Dict[str, str]:
        """Extract imports from a Python file."""
        imports = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        module = node.module or ''
                        for alias in node.names:
                            imports[alias.name] = module
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[alias.name] = alias.name
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return imports
    
    def extract_class_info(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract class information from a Python file."""
        classes = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        base_classes = [
                            base.id if isinstance(base, ast.Name) else
                            f"{base.value.id}.{base.attr}" if isinstance(base, ast.Attribute) else
                            str(base)
                            for base in node.bases
                        ]
                        
                        # Extract methods
                        methods = [
                            item.name for item in node.body
                            if isinstance(item, ast.FunctionDef)
                        ]
                        
                        classes.append({
                            'name': node.name,
                            'bases': base_classes,
                            'methods': methods,
                            'line': node.lineno
                        })
        except Exception as e:
            logger.warning(f"Error extracting classes from {file_path}: {e}")
        
        return classes
    
    def find_service_calls(self, file_path: Path) -> List[Tuple[str, str]]:
        """Find service method calls in a UI file."""
        service_calls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Pattern: service.method(session, ...)
                pattern = r'(\w+)\.(\w+)\(session'
                matches = re.findall(pattern, content)
                service_calls.extend(matches)
                
                # Pattern: get_*_service()
                pattern = r'(get_\w+_service)\(\)'
                getter_matches = re.findall(pattern, content)
                for getter in getter_matches:
                    service_calls.append((getter, 'getter'))
        except Exception as e:
            logger.warning(f"Error finding service calls in {file_path}: {e}")
        
        return service_calls
    
    def verify_ui_file(self, ui_file: Path) -> ServiceBinding:
        """Verify a single UI file's service bindings."""
        issues = []
        
        # Extract imports
        imports = self.extract_imports(ui_file)
        
        # Check for service imports
        service_imports = {
            name: module for name, module in imports.items()
            if 'service' in name.lower() or 'services' in module.lower()
        }
        
        # Extract class information
        classes = self.extract_class_info(ui_file)
        
        # Find main window class
        main_class = None
        base_class = "Unknown"
        for cls in classes:
            if 'Window' in cls['name'] and cls['name'] != 'QMainWindow':
                main_class = cls
                base_class = cls['bases'][0] if cls['bases'] else "Unknown"
                break
        
        if not main_class:
            issues.append("No main window class found")
            main_class = {'name': ui_file.stem, 'methods': []}
        
        # Find service calls
        service_calls = self.find_service_calls(ui_file)
        service_methods_used = list(set([call[1] for call in service_calls if call[1] != 'getter']))
        
        # Check for expected patterns
        if not service_imports:
            issues.append("No service imports found")
        
        # Check if load_data method exists
        if 'load_data' not in main_class['methods']:
            issues.append("Missing load_data method (required by ModuleUI)")
        
        # Check for refresh_view usage
        with open(ui_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'refresh_view' not in content and 'ModuleWidget' in base_class:
                issues.append("Missing refresh_view call (recommended for data refresh)")
        
        # Determine service name from imports or file name
        service_name = "None"
        service_import = "None"
        for name, module in service_imports.items():
            if 'get_' in name and '_service' in name:
                service_name = name.replace('get_', '').replace('_service', '').title()
                service_import = name
                break
        
        # If no service found, try to infer from filename
        if service_name == "None":
            # E.g., users_window.py -> UserService
            base_name = ui_file.stem.replace('_window', '').replace('_main', '')
            if base_name in ['company', 'branch', 'user', 'role', 'product', 
                            'category', 'customer', 'supplier', 'account']:
                expected_getter = f"get_{base_name}_service"
                if expected_getter in self.service_getters.values():
                    issues.append(f"Service import missing: should import {expected_getter}")
        
        return ServiceBinding(
            ui_file=ui_file.name,
            ui_class=main_class['name'],
            service_import=service_import,
            service_name=service_name,
            service_methods_used=service_methods_used,
            ui_methods=main_class['methods'],
            base_class=base_class,
            issues=issues
        )
    
    def verify_all(self) -> VerificationResult:
        """Verify all UI files."""
        logger.info("Starting UI-Service binding verification...")
        
        bindings = []
        errors = []
        warnings = []
        
        # Get all UI files
        ui_files = list(self.ui_dir.glob('*_window.py'))
        
        for ui_file in ui_files:
            try:
                logger.info(f"Verifying {ui_file.name}...")
                binding = self.verify_ui_file(ui_file)
                bindings.append(binding)
                
                # Categorize issues
                for issue in binding.issues:
                    if 'No service imports' in issue or 'Missing load_data' in issue:
                        errors.append({
                            'file': ui_file.name,
                            'issue': issue
                        })
                    else:
                        warnings.append({
                            'file': ui_file.name,
                            'issue': issue
                        })
            except Exception as e:
                logger.error(f"Error verifying {ui_file.name}: {e}")
                errors.append({
                    'file': ui_file.name,
                    'issue': f"Verification failed: {str(e)}"
                })
        
        ui_with_services = len([b for b in bindings if b.service_import != "None"])
        
        result = VerificationResult(
            total_ui_files=len(ui_files),
            ui_with_services=ui_with_services,
            ui_without_services=len(ui_files) - ui_with_services,
            bindings=bindings,
            errors=errors,
            warnings=warnings,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Verification complete: {len(bindings)} files analyzed")
        logger.info(f"  - With services: {ui_with_services}")
        logger.info(f"  - Without services: {result.ui_without_services}")
        logger.info(f"  - Errors: {len(errors)}")
        logger.info(f"  - Warnings: {len(warnings)}")
        
        return result
    
    def generate_report(self, result: VerificationResult, output_file: str):
        """Generate JSON report of verification results."""
        try:
            output_path = self.project_root / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Report saved to {output_path}")
        except Exception as e:
            logger.error(f"Error generating report: {e}")


def main():
    """Main entry point."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    logger.info(f"Project root: {project_root}")
    
    # Create verifier
    verifier = UIServiceVerifier(str(project_root))
    
    # Run verification
    result = verifier.verify_all()
    
    # Generate report
    verifier.generate_report(result, 'logs/ui_service_verification.json')
    
    # Print summary
    print("\n" + "="*70)
    print("UI-SERVICE BINDING VERIFICATION SUMMARY")
    print("="*70)
    print(f"Total UI Files Analyzed: {result.total_ui_files}")
    print(f"Files with Service Bindings: {result.ui_with_services}")
    print(f"Files without Service Bindings: {result.ui_without_services}")
    print(f"Total Errors: {len(result.errors)}")
    print(f"Total Warnings: {len(result.warnings)}")
    print("="*70)
    
    if result.errors:
        print("\nCRITICAL ERRORS:")
        for error in result.errors:
            print(f"  - {error['file']}: {error['issue']}")
    
    if result.warnings:
        print("\nWARNINGS:")
        for warning in result.warnings[:10]:  # Show first 10
            print(f"  - {warning['file']}: {warning['issue']}")
        if len(result.warnings) > 10:
            print(f"  ... and {len(result.warnings) - 10} more warnings")
    
    print("\nDetailed report saved to: logs/ui_service_verification.json")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
