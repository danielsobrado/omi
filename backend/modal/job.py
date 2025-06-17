import json
import os
import asyncio

from utils.other.notifications import start_cron_job

# Initialize Firebase only if we're using Firestore database
DATABASE_CHOICE = os.getenv("DATABASE_CHOICE", "firestore")
if DATABASE_CHOICE == "firestore":
    import firebase_admin
    
    if os.environ.get('SERVICE_ACCOUNT_JSON'):
        service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
        credentials = firebase_admin.credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(credentials)
    else:
        firebase_admin.initialize_app()
    print(f"Firebase Admin initialized for database choice: {DATABASE_CHOICE}")
else:
    print(f"Skipping Firebase Admin initialization for database choice: {DATABASE_CHOICE}")

print('Starting cron job...')
asyncio.run(start_cron_job())
