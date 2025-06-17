import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_user():
    """
    Creates the basic auth user in the database if it doesn't exist.
    """
    # Load environment variables from .env file
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Set the database choice to postgres for this script
    os.environ["DATABASE_CHOICE"] = "postgres"

    from database.users import create_user_if_not_exists

    uid = os.getenv("BASIC_AUTH_UID")
    username = os.getenv("BASIC_AUTH_USERNAME")
    
    if not uid or not username:
        print("Error: BASIC_AUTH_UID and BASIC_AUTH_USERNAME must be set in your .env file.")
        return

    print(f"Attempting to create user '{username}' with UID '{uid}'...")
    
    try:
        user = create_user_if_not_exists(
            uid=uid,
            email=f"{username}@example.com",  # Using a placeholder email
            display_name=username.capitalize()
        )
        if user:
            print(f"Successfully created or found user: {user.uid}")
        else:
            print("Failed to create user.")
    except Exception as e:
        print(f"An error occurred while seeding the user: {e}")

if __name__ == "__main__":
    seed_user()
