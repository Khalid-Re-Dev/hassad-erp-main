"""Test authentication and session logging after fix."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import get_db_context
from core.auth import authenticate_user, InvalidCredentialsError
from models.session_log import SessionLog
from sqlalchemy import func

def test_successful_login():
    """Test successful login creates session log entry."""
    print("🔍 Testing successful login...")
    
    # Count existing session logs
    with get_db_context() as db:
        initial_count = db.query(func.count(SessionLog.id)).scalar()
        print(f"Initial session log count: {initial_count}")
    
    # Attempt successful login
    try:
        with get_db_context() as db:
            user = authenticate_user(
                session=db,
                username="admin",
                password="admin123",
                ip_address="127.0.0.1",
                user_agent="Test Client"
            )
            print(f"✅ Login successful for user: {user.username}")
            
        # Check if session log was created and committed
        with get_db_context() as db:
            final_count = db.query(func.count(SessionLog.id)).scalar()
            print(f"Final session log count: {final_count}")
            
            # Get the latest session log
            latest_log = db.query(SessionLog).order_by(SessionLog.login_time.desc()).first()
            if latest_log:
                print(f"✅ Latest session log:")
                print(f"   - User ID: {latest_log.user_id}")
                print(f"   - Success: {latest_log.success}")
                print(f"   - IP Address: {latest_log.ip_address}")
                print(f"   - User Agent: {latest_log.user_agent}")
                print(f"   - Session Token: {latest_log.session_token}")
                
        if final_count > initial_count:
            print("✅ SUCCESS: Session log entry was committed!")
            return True
        else:
            print("❌ FAIL: No new session log entry found!")
            return False
            
    except Exception as e:
        print(f"❌ Error during successful login test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_failed_login():
    """Test failed login creates session log entry."""
    print("\n🔍 Testing failed login...")
    
    # Count existing session logs
    with get_db_context() as db:
        initial_count = db.query(func.count(SessionLog.id)).scalar()
        print(f"Initial session log count: {initial_count}")
    
    # Attempt failed login
    try:
        with get_db_context() as db:
            user = authenticate_user(
                session=db,
                username="admin",
                password="wrong_password",
                ip_address="127.0.0.1",
                user_agent="Test Client"
            )
            print("❌ This should not happen - login should have failed!")
            return False
            
    except InvalidCredentialsError:
        print("✅ Login correctly failed with InvalidCredentialsError")
        
        # Check if session log was created and committed
        with get_db_context() as db:
            final_count = db.query(func.count(SessionLog.id)).scalar()
            print(f"Final session log count: {final_count}")
            
            # Get the latest session log
            latest_log = db.query(SessionLog).order_by(SessionLog.login_time.desc()).first()
            if latest_log:
                print(f"✅ Latest session log:")
                print(f"   - User ID: {latest_log.user_id}")
                print(f"   - Success: {latest_log.success}")
                print(f"   - Failure Reason: {latest_log.failure_reason}")
                print(f"   - IP Address: {latest_log.ip_address}")
                
        if final_count > initial_count:
            print("✅ SUCCESS: Failed login session log entry was committed!")
            return True
        else:
            print("❌ FAIL: No new session log entry found for failed login!")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error during failed login test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all authentication tests."""
    print("🚀 HASSAD ERP - AUTHENTICATION & SESSION LOGGING TESTS")
    print("=" * 60)
    
    success_test = test_successful_login()
    failed_test = test_failed_login()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"✅ Successful Login Test: {'PASS' if success_test else 'FAIL'}")
    print(f"✅ Failed Login Test: {'PASS' if failed_test else 'FAIL'}")
    
    if success_test and failed_test:
        print("\n🎉 ALL TESTS PASSED! Authentication and session logging are working correctly.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED! Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)