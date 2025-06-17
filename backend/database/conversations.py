import os

# Read the environment variable to decide which database implementation to use.
# Default to 'firestore' if not set.
DATABASE_CHOICE = os.getenv("DATABASE_CHOICE", "firestore")

print(f"Using {DATABASE_CHOICE} database implementation for conversations.")

if DATABASE_CHOICE == "postgres":
    from .postgres.conversations import *
elif DATABASE_CHOICE == "firestore":
    from .firestore.conversations import *
else:
    raise ValueError(f"Unsupported DATABASE_CHOICE: {DATABASE_CHOICE}")
