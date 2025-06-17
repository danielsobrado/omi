import json
import os

from modal import Image, App, Secret, Cron
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

app = App(
    name='job',
    secrets=[Secret.from_name("gcp-credentials"), Secret.from_name('envs')],
)
image = (
    Image.debian_slim()
    .apt_install('ffmpeg', 'git', 'unzip')
    .pip_install_from_requirements('requirements.txt')
)

@app.function(image=image, schedule=Cron('* * * * *'))
async def notifications_cronjob():
    await start_cron_job()
