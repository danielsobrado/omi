import json
import os

from fastapi import FastAPI

import modal
from modal import Image, App, asgi_app, Secret
from routers import pusher

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

app = FastAPI()
app.include_router(pusher.router)

modal_app = App(
    name='pusher',
    secrets=[Secret.from_name("gcp-credentials"), Secret.from_name('envs')],
)
image = (
    Image.debian_slim()
    .apt_install('ffmpeg', 'git', 'unzip')
    .pip_install_from_requirements('requirements.txt')
)


@modal_app.function(
    image=image,
    min_containers=2,
    memory=(512, 1024),
    cpu=2,
    timeout=60 * 10,
)
@modal.concurrent(max_inputs=10)
@asgi_app()
def api():
    return app

paths = ['_temp', '_samples', '_segments', '_speech_profiles']
for path in paths:
    if not os.path.exists(path):
        os.makedirs(path)
