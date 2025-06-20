# backend/database/postgres/tasks.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from .client import db_session_manager
from .models import Task as TaskModel

@db_session_manager
def create_task(db: Session, uid: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    task = TaskModel(uid=uid, **task_data)
    db.add(task)
    db.flush()
    return {c.name: getattr(task, c.name) for c in task.__table__.columns}

@db_session_manager
def get_tasks(db: Session, uid: str, completed: bool = None, limit: int = 100) -> List[Dict[str, Any]]:
    query = db.query(TaskModel).filter(TaskModel.uid == uid)
    if completed is not None:
        query = query.filter(TaskModel.completed == completed)
    tasks = query.order_by(desc(TaskModel.created_at)).limit(limit).all()
    return [{c.name: getattr(task, c.name) for c in task.__table__.columns} for task in tasks]

@db_session_manager
def get_task(db: Session, task_id: str) -> Optional[Dict[str, Any]]:
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if task:
        return {c.name: getattr(task, c.name) for c in task.__table__.columns}
    return None

@db_session_manager
def update_task(db: Session, task_id: str, task_data: dict) -> bool:
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if task:
        for key, value in task_data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return True
    return False

def complete_task(task_id: str) -> bool:
    return update_task(task_id, {'completed': True, 'completed_at': datetime.utcnow()})

@db_session_manager
def delete_task(db: Session, task_id: str) -> bool:
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if task:
        db.delete(task)
        return True
    return False

@db_session_manager
def get_task_count(db: Session, uid: str, completed: bool = None) -> int:
    query = db.query(TaskModel).filter(TaskModel.uid == uid)
    if completed is not None:
        query = query.filter(TaskModel.completed == completed)
    return query.count()