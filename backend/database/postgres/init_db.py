# backend/database/postgres/init_db.py
from .client import Base, engine
from .models import User, App, Conversation, Memory, Message, Notification, Task, AuthToken

def init_database():
    print("Initializing PostgreSQL database and creating tables...")
    # This creates all tables defined in models.py that inherit from Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_database()
