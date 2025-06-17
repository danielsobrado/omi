import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from utils.other.endpoints import get_current_user_uid

# Load environment variables from .env file
load_dotenv()

# Set the database choice to postgres
os.environ["DATABASE_CHOICE"] = "postgres"
os.environ["POSTGRES_URL"] = "postgresql://unspsc:unspsc@localhost:5433/unspsc"

app = FastAPI(title="Omi Backend - Basic Auth Test")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

@app.get("/protected", tags=["Test"])
def protected_endpoint(uid: str = Depends(get_current_user_uid)):
    return {"message": "Authentication successful!", "uid": uid}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
