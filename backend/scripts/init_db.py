import logging
from sqlalchemy.orm import Session
from app.infrastructure.database import engine, Base, SessionLocal
from app.domain import models
from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    user = db.query(models.User).filter(models.User.email == "admin@classflow.local").first()
    if not user:
        user = models.User(
            email="admin@classflow.local",
            hashed_password=security.get_password_hash("admin123"),
            name="Default Admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created default admin user: {user.email} / admin123")
    else:
        logger.info("Admin user already exists")

def main() -> None:
    print("Starting database initialization...")
    logger.info("Creating initial data")
    db = SessionLocal()
    init_db(db)
    logger.info("Initial data created")
    print("Database initialization finished successfully!")

if __name__ == "__main__":
    main()
