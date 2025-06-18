import asyncio
import json
import os

from fastapi import FastAPI

# Conditional import for APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    print("Warning: APScheduler not available. Cron jobs will be disabled.")
    print("Install with: pip install apscheduler")
    SCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None

# Import all your existing and new routers
from routers import (
    workflow, chat, firmware, plugins, transcribe, notifications,
    speech_profile, agents, users, trends, sync, apps, 
    # custom_auth, # REMOVE
    payment, integration, conversations, memories, mcp, 
    # oauth, # REMOVE
    modal_services,  # NEW: Contains speaker identification and VAD
)
from utils.other.timeout import TimeoutMiddleware
from utils.other.notifications import start_cron_job

# --- Database Initialization ---
# Check which database is configured and initialize if necessary.
if os.getenv("DATABASE_CHOICE") == "postgres":
    from database.postgres.init_db import init_database
    # This will create the database tables if they don't exist on startup.
    init_database()

# REMOVE THE ENTIRE FIREBASE INITIALIZATION BLOCK
# No longer needed for authentication

app = FastAPI(title="Omi Backend")

# --- Local Cron Job Setup (Replaces Modal Cron) ---
scheduler = AsyncIOScheduler() if SCHEDULER_AVAILABLE else None

@app.on_event("startup")
async def startup_event():
    if SCHEDULER_AVAILABLE and scheduler:
        # Schedule the job to run every minute, just like the Modal Cron
        scheduler.add_job(start_cron_job, 'cron', minute='*')
        scheduler.start()
        print("AsyncIOScheduler started for cron jobs.")
    else:
        print("APScheduler not available. Cron jobs disabled. Install with: pip install apscheduler")

@app.on_event("shutdown")
def shutdown_event():
    if SCHEDULER_AVAILABLE and scheduler:
        scheduler.shutdown()
        print("AsyncIOScheduler shut down.")
    else:
        print("No scheduler to shut down.")

# --- Include all API Routers ---
app.include_router(transcribe.router)
app.include_router(conversations.router)
app.include_router(memories.router)
app.include_router(chat.router)
app.include_router(plugins.router)
app.include_router(speech_profile.router)
app.include_router(modal_services.router)  # NEW: Modal services (speaker identification, VAD)
# app.include_router(screenpipe.router)
app.include_router(notifications.router)
app.include_router(workflow.router)
app.include_router(integration.router)
app.include_router(agents.router)
app.include_router(users.router)
app.include_router(trends.router)

app.include_router(firmware.router)
app.include_router(sync.router)

app.include_router(apps.router)
# app.include_router(custom_auth.router) # REMOVE
# app.include_router(oauth.router) # REMOVE

app.include_router(payment.router)
app.include_router(mcp.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


methods_timeout = {
    "GET": os.environ.get('HTTP_GET_TIMEOUT'),
    "PUT": os.environ.get('HTTP_PUT_TIMEOUT'),
    "PATCH": os.environ.get('HTTP_PATCH_TIMEOUT'),
    "DELETE": os.environ.get('HTTP_DELETE_TIMEOUT'),
}

app.add_middleware(TimeoutMiddleware, methods_timeout=methods_timeout)

# Create temporary directories if they don't exist
paths = ['_temp', '_samples', '_segments', '_speech_profiles']
for path in paths:
    if not os.path.exists(path):
        os.makedirs(path)
