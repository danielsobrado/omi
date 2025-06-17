import os

# Read the environment variable to decide which database implementation to use.
# Default to 'firestore' if not set.
DATABASE_CHOICE = os.getenv("DATABASE_CHOICE", "firestore")

if DATABASE_CHOICE == "postgres":
    print("Using PostgreSQL database implementation for vector_db.")
    from .postgres.vector_db import *
else:
    print("Using Firestore database implementation for vector_db.")
    from .firestore.vector_db import *