from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#  The Connection URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./switchboard.db"


#  Create the Engine (The connection to the file)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


#  Create a Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#  The Base Class (All our tables will inherit from this)
Base = declarative_base()

#  Dependency Injection (This function gives the API a database session and closes it when done)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()