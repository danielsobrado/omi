import asyncio
import math
import os

import database.notifications as notification_db

# Check database choice to determine notification method
DATABASE_CHOICE = os.getenv("DATABASE_CHOICE", "firestore")

def send_notification(token: str, title: str, body: str, data: dict = None):
    """Send notification using the configured backend"""
    if DATABASE_CHOICE == "firestore":
        return _send_firebase_notification(token, title, body, data)
    else:
        return _send_postgres_notification(token, title, body, data)

def _send_firebase_notification(token: str, title: str, body: str, data: dict = None):
    """Send notification using Firebase Cloud Messaging"""
    try:
        from firebase_admin import messaging
        
        print('send_notification (Firebase)')
        notification = messaging.Notification(title=title, body=body)
        message = messaging.Message(notification=notification, token=token)

        if data:
            message.data = data

        response = messaging.send(message)
        print('send_notification success:', response)
        return response
    except Exception as e:
        error_message = str(e)
        if "Requested entity was not found" in error_message:
            notification_db.remove_token(token)
        print('send_notification failed:', e)
        raise

def _send_postgres_notification(token: str, title: str, body: str, data: dict = None):
    """Send notification using PostgreSQL backend (store for later delivery)"""
    try:
        print('send_notification (PostgreSQL - storing notification)')
        
        # Store notification in database for later delivery
        # This can be processed by a background service or webhook
        notification_data = {
            'title': title,
            'body': body,
            'data': data or {},
            'token': token,
            'status': 'pending'
        }
        
        # For PostgreSQL mode, we'll store the notification 
        # A separate service can process these notifications
        notification_db.store_pending_notification(notification_data)
        print('send_notification success: notification stored in database')
        return "stored"
    except Exception as e:
        print('send_notification failed:', e)
        raise


async def send_bulk_notification(user_tokens: list, title: str, body: str):
    try:
        batch_size = 500
        num_batches = math.ceil(len(user_tokens) / batch_size)

        def send_batch(batch_users):
            messages = [
                messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    token=token
                ) for token in batch_users
            ]
            return messaging.send_each(messages)

        tasks = []
        for i in range(num_batches):
            start = i * batch_size
            end = start + batch_size
            batch_users = user_tokens[start:end]
            task = asyncio.to_thread(send_batch, batch_users)
            tasks.append(task)

        await asyncio.gather(*tasks)

    except Exception as e:
        print("Error sending message:", e)
