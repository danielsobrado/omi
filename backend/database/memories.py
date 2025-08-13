import os

DATABASE_CHOICE = os.getenv("DATABASE_CHOICE", "firestore")

if DATABASE_CHOICE == "postgres":
    print("Using PostgreSQL database implementation for memories.")
    from .postgres.memories import *
else:
    print("Using Firestore database implementation for memories.")
    from .firestore.memories import *
