import os

DATABASE_CHOICE = os.getenv("DATABASE_CHOICE", "firestore")

if DATABASE_CHOICE == "postgres":
    print("Using PostgreSQL database implementation for users.")
    from .postgres.users import *
else:
    print("Using Firestore database implementation for users.")
    from .firestore.users import *