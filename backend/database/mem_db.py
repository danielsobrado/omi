import os

# Read the environment variable to decide which database implementation to use.
# Default to 'firestore' if not set.
DATABASE_CHOICE = os.getenv("DATABASE_CHOICE", "firestore")

if DATABASE_CHOICE == "postgres":
    print("Using PostgreSQL database implementation for mem_db.")
    from .postgres.mem_db import *
else:
    print("Using Firestore database implementation for mem_db.")
    from .firestore.mem_db import *
