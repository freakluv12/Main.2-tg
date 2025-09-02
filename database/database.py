from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import config

# Создаем движок базы данных
engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Используем Base из models.py
from .models import Base


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sync_db():
    """Synchronous database session for bot"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Caller должен сам закрыть сессию


# Для совместимости со старым кодом
async def get_async_db():
    """Async-compatible database session for bot"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
