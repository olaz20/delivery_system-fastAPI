from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker
from .config import settings
from app.core import security


SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db():
    db = SessionLocal()
    try:
        security.initialize_default_admin(db)
        yield db
    finally:
        db.close()