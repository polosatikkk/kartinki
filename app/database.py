from sqlalchemy import create_engine
from app.config import DATABASE_URL
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
class Base(DeclarativeBase): pass
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()