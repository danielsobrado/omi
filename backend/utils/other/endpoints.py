import json
import os
import time
import base64
import binascii
from fastapi import Header, HTTPException
from fastapi import Request

# We no longer need firebase_admin for authentication here
# from firebase_admin import auth
# from firebase_admin.auth import InvalidIdTokenError


def get_user_from_db(uid: str):
    # This is a simplified placeholder. In a real app, you'd query your DB.
    # For now, we just need to ensure the hardcoded user is recognized.
    if uid == os.getenv("BASIC_AUTH_UID"):
        return {"uid": uid, "email": "user@example.com"}  # Return some mock data
    return None


def get_current_user_uid(authorization: str = Header(None)):
    if authorization and os.getenv('ADMIN_KEY') and os.getenv('ADMIN_KEY') in authorization:
        return authorization.split(os.getenv('ADMIN_KEY'))[1]

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header not found")

    # --- Start of Basic Auth Logic ---
    try:
        auth_scheme, credentials = authorization.split(" ", 1)
        if auth_scheme.lower() != "basic":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme. Use Basic Auth.")

        decoded_credentials = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)

        # Get expected credentials from environment variables
        expected_username = os.getenv("BASIC_AUTH_USERNAME")
        expected_password = os.getenv("BASIC_AUTH_PASSWORD")
        hardcoded_uid = os.getenv("BASIC_AUTH_UID")

        if not all([expected_username, expected_password, hardcoded_uid]):
             raise ConnectionError("Basic Auth environment variables not set on the server.")

        # Validate credentials
        if username == expected_username and password == expected_password:
            return hardcoded_uid
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")

    except HTTPException:
        # Re-raise HTTPException as-is, don't convert to 500
        raise
    except (ValueError, TypeError, binascii.Error) as e:
        raise HTTPException(status_code=401, detail=f"Invalid Basic Auth credentials: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # --- End of Basic Auth Logic ---


cached = {}


def rate_limit_custom(endpoint: str, request: Request, requests_per_window: int, window_seconds: int):
    ip = request.client.host
    key = f"rate_limit:{endpoint}:{ip}"

    # Check if the IP is already rate-limited
    current = cached.get(key)
    if current:
        current = json.loads(current)
        remaining = current["remaining"]
        timestamp = current["timestamp"]
        current_time = int(time.time())

        # Check if the time window has expired
        if current_time - timestamp >= window_seconds:
            remaining = requests_per_window - 1  # Reset the counter for the new window
            timestamp = current_time
        elif remaining == 0:
            raise HTTPException(status_code=429, detail="Too Many Requests")

        remaining -= 1

    else:
        # If no previous data found, start a new time window
        remaining = requests_per_window - 1
        timestamp = int(time.time())

    # Update the rate limit info in Redis
    current = {"timestamp": timestamp, "remaining": remaining}
    cached[key] = json.dumps(current)

    return True


# Dependency to enforce custom rate limiting for specific endpoints
def rate_limit_dependency(endpoint: str = "", requests_per_window: int = 60, window_seconds: int = 60):
    def rate_limit(request: Request):
        return rate_limit_custom(endpoint, request, requests_per_window, window_seconds)

    return rate_limit


def timeit(func):
    """
    Decorator for measuring function's running time.
    """

    def measure_time(*args, **kw):
        start_time = time.time()
        result = func(*args, **kw)
        print("Processing time of %s(): %.2f seconds."
              % (func.__qualname__, time.time() - start_time))
        return result

    return measure_time


def delete_account(uid: str):
    # This function would now delete from your PostgreSQL database
    from database.users import delete_user
    delete_user(uid)
    return {"message": "User deleted"}
