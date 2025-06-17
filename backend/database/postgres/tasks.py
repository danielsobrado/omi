# backend/database/postgres/tasks.py
from datetime import datetime
from typing import List
from sqlalchemy import desc, and_
from .client import get_db_session
from .models import Task as TaskModel


def create_task(uid: str, task_data: dict):
    """Create a new task"""
    db = get_db_session()
    try:
        task = TaskModel(uid=uid, **task_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return {c.name: getattr(task, c.name) for c in task.__table__.columns}
    finally:
        db.close()


def get_tasks(uid: str, completed: bool = None, limit: int = 100):
    """Get tasks for a user"""
    db = get_db_session()
    try:
        query = db.query(TaskModel).filter(TaskModel.uid == uid)
        
        if completed is not None:
            query = query.filter(TaskModel.completed == completed)
            
        tasks = (
            query.order_by(desc(TaskModel.created_at))
            .limit(limit)
            .all()
        )
        return [{c.name: getattr(task, c.name) for c in task.__table__.columns} for task in tasks]
    finally:
        db.close()


def get_task(task_id: str):
    """Get a specific task"""
    db = get_db_session()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            return {c.name: getattr(task, c.name) for c in task.__table__.columns}
        return None
    finally:
        db.close()


def update_task(task_id: str, task_data: dict):
    """Update a task"""
    db = get_db_session()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            for key, value in task_data.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def complete_task(task_id: str):
    """Mark a task as completed"""
    db = get_db_session()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            task.completed = True
            task.completed_at = datetime.utcnow()
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_task(task_id: str):
    """Delete a task"""
    db = get_db_session()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_task_count(uid: str, completed: bool = None):
    """Get task count for a user"""
    db = get_db_session()
    try:
        query = db.query(TaskModel).filter(TaskModel.uid == uid)
        
        if completed is not None:
            query = query.filter(TaskModel.completed == completed)
            
        return query.count()
    finally:
        db.close()
