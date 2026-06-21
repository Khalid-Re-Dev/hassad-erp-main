"""
Test Tab Rendering and Widget Display.

Validates that module widgets are properly displayed in the QStackedWidget.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QStackedWidget
from PyQt6.QtCore import Qt

# Create QApplication before importing UI modules
if not QApplication.instance():
    app = QApplication(sys.argv)

from ui.main_window import MODULE_REGISTRY
from ui.ui_helpers import wrap_window_for_embedding
from core.database import SessionLocal
from core.permissions import permission_manager


def test_widget_wrapping():
    """Test that QMainWindow widgets are properly wrapped."""
    print("🧪 Testing widget wrapping...")
    
    # Create mock app context
    app_context = {
        'session_factory': SessionLocal,
        'current_user': None,
        'current_company': None,
        'current_branch': None,
        'permission_manager': permission_manager
    }
    
    # Test a few modules
    test_modules = ['products', 'users', 'reports']
    
    for module_id in test_modules:
        if module_id not in MODULE_REGISTRY:
            continue
            
        module_path, class_name, permission = MODULE_REGISTRY[module_id]
        print(f"\n  Testing {module_id}: {class_name}")
        
        try:
            # Import module
            import importlib
            module = importlib.import_module(module_path)
            widget_class = getattr(module, class_name)
            
            # Instantiate
            widget = widget_class(app_context=app_context)
            print(f"    ✅ Instantiated {class_name}")
            
            # Test wrapping
            from PyQt6.QtWidgets import QMainWindow
            if isinstance(widget, QMainWindow):
                wrapped = wrap_window_for_embedding(widget)
                print(f"    ✅ Wrapped QMainWindow → {wrapped.__class__.__name__}")
                assert wrapped is not widget, "Wrapped widget should be different from original"
            else:
                wrapped = wrap_window_for_embedding(widget)
                print(f"    ✅ QWidget passed through (no wrapping needed)")
                assert wrapped is widget, "QWidget should not be wrapped"
            
            # Test adding to stack
            stack = QStackedWidget()
            idx = stack.addWidget(wrapped)
            stack.setCurrentIndex(idx)
            print(f"    ✅ Added to QStackedWidget at index {idx}")
            
            # Verify visibility
            assert stack.currentWidget() is wrapped, "Current widget mismatch"
            print(f"    ✅ Widget is current in stack")
            
        except Exception as e:
            print(f"    ❌ FAILED: {str(e)}")
            raise


def test_stack_widget_count():
    """Test that widgets are properly managed in stack."""
    print("\n🧪 Testing stack widget management...")
    
    stack = QStackedWidget()
    initial_count = stack.count()
    print(f"  Initial stack count: {initial_count}")
    
    # Add welcome page
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
    welcome = QWidget()
    layout = QVBoxLayout(welcome)
    layout.addWidget(QLabel("Welcome"))
    stack.addWidget(welcome)
    
    print(f"  After adding welcome: {stack.count()}")
    assert stack.count() == initial_count + 1
    
    # Switch between widgets
    from PyQt6.QtWidgets import QWidget as W2
    test_widget = W2()
    idx = stack.addWidget(test_widget)
    stack.setCurrentIndex(idx)
    
    print(f"  After adding module widget: {stack.count()}")
    assert stack.count() == initial_count + 2
    assert stack.currentWidget() is test_widget
    print(f"  ✅ Stack management working correctly")


def main():
    """Run all tests."""
    print("="*60)
    print("TAB RENDERING VALIDATION TESTS")
    print("="*60)
    
    try:
        test_widget_wrapping()
        test_stack_widget_count()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        return 0
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TESTS FAILED: {str(e)}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
