from core.database import get_db_context
from models.session_log import SessionLog
from sqlalchemy import func

with get_db_context() as db:
    count = db.query(func.count(SessionLog.id)).scalar()
    print(f"Total session logs: {count}")
    
    # Show latest 3 session logs
    logs = db.query(SessionLog).order_by(SessionLog.login_time.desc()).limit(3).all()
    for i, log in enumerate(logs, 1):
        print(f"\n{i}. Session {log.id}")
        print(f"   User ID: {log.user_id}")
        print(f"   Success: {log.success}")
        print(f"   IP: {log.ip_address}")
        print(f"   User Agent: {log.user_agent}")
        if log.success:
            print(f"   Session Token: {log.session_token}")
        else:
            print(f"   Failure Reason: {log.failure_reason}")