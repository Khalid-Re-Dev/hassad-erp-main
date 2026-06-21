"""
Test Navigation Triggering Diagnosis

This script patches the main_window to add diagnostic output at the signal connection point.
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def analyze_signal_connection():
    """Analyze the signal connection code."""
    import inspect
    from ui.main_window import MainWindow
    from models import User
    
    # Get the _create_sidebar method
    create_sidebar_source = inspect.getsource(MainWindow._create_sidebar)
    
    print("=" * 80)
    print("ANALYZING SIGNAL CONNECTION IN _create_sidebar()")
    print("=" * 80)
    
    # Check if itemClicked.connect is present
    if "itemClicked.connect" in create_sidebar_source:
        print("✅ itemClicked.connect found in _create_sidebar")
        
        # Extract the line
        for line in create_sidebar_source.split('\n'):
            if "itemClicked.connect" in line:
                print(f"\nConnection line: {line.strip()}")
    else:
        print("❌ itemClicked.connect NOT found in _create_sidebar")
    
    print("\n" + "=" * 80)
    print("ANALYZING _navigate_to_module METHOD")
    print("=" * 80)
    
    # Get the _navigate_to_module method
    navigate_source = inspect.getsource(MainWindow._navigate_to_module)
    
    # Check if routing_logger.info is at the start
    if "routing_logger.info" in navigate_source:
        lines = navigate_source.split('\n')
        for i, line in enumerate(lines[:10]):  # First 10 lines
            if "routing_logger.info" in line:
                print(f"✅ Logging found at line {i}: {line.strip()}")
                break
    
    print("\n" + "=" * 80)
    print("CHECKING MODULE_REGISTRY")
    print("=" * 80)
    
    from ui.main_window import MODULE_REGISTRY
    print(f"✅ MODULE_REGISTRY contains {len(MODULE_REGISTRY)} modules")
    print("\nModules:", list(MODULE_REGISTRY.keys())[:5], "...")

if __name__ == "__main__":
    try:
        analyze_signal_connection()
        print("\n" + "=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)
        print("\nNext step: Run 'python main.py', click a tab, and check:")
        print("1. Does logs/ui_routing.log get created?")
        print("2. Does console show DEBUG OUTPUT?")
        print("3. Do error dialogs appear?")
        print("\nIf NONE of these happen, the signal is not firing.")
        
    except Exception as e:
        print(f"\n❌ ERROR during diagnosis: {e}")
        import traceback
        traceback.print_exc()
