from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    
    # Check for existing tables and columns
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # If the 'users' table exists, check for the 'phone_number' column
    if 'users' in existing_tables:
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'phone_number' not in columns:
            print("Adding missing 'phone_number' column...")
            with engine.connect() as connection:
                connection.execute("ALTER TABLE users ADD COLUMN phone_number TEXT;")
        else:
            print("'phone_number' column already exists.")
    else:
        print("'users' table does not exist. Creating table...")
        Base.metadata.create_all(bind=engine)
