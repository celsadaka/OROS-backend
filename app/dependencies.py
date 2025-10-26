from sqlalchemy.orm import Session
from .database import SessionLocal

def get_db() -> Session:
    """Provide a transactional scope for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
