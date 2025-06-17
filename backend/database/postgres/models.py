# backend/database/postgres/models.py
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, Text, ForeignKey, JSON, Integer, 
    func, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from datetime import datetime
import uuid
from .client import Base


class User(Base):
    __tablename__ = "users"
    
    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    display_name = Column(String)
    fcm_token = Column(String, nullable=True)  # Firebase Cloud Messaging token for notifications
    time_zone = Column(String, nullable=True, default='UTC')  # User's timezone for notifications
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    apps = relationship("App", back_populates="owner")
    conversations = relationship("Conversation", back_populates="user")
    memories = relationship("Memory", back_populates="user")


class App(Base):
    __tablename__ = "apps"
    
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), nullable=True, index=True)
    name = Column(String, index=True)
    private = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    status = Column(String, default='approved')
    category = Column(String)
    email = Column(String)
    author = Column(String)
    description = Column(Text)
    image = Column(String)
    capabilities = Column(ARRAY(String))
    memory_prompt = Column(Text)
    chat_prompt = Column(Text)
    persona_prompt = Column(Text)
    username = Column(String)
    connected_accounts = Column(ARRAY(String), default=[])
    twitter = Column(JSON)
    external_integration = Column(JSON)
    reviews = Column(JSON, default=[])
    user_review = Column(JSON)
    rating_avg = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=False)
    trigger_workflow_memories = Column(Boolean, default=True)
    installs = Column(Integer, default=0)
    proactive_notification = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    money_made = Column(Float)
    usage_count = Column(Integer)
    is_paid = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    payment_plan = Column(String)
    payment_product_id = Column(String)
    payment_price_id = Column(String)
    payment_link_id = Column(String)
    payment_link = Column(String)
    is_user_paid = Column(Boolean, default=False)
    thumbnails = Column(ARRAY(String))
    thumbnail_urls = Column(ARRAY(String))
    is_influencer = Column(Boolean, default=False)
    is_popular = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", back_populates="apps")
    usage_history = relationship("AppUsageHistory", back_populates="app")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), index=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    structured = Column(JSON)
    transcript_segments = Column(JSON)
    discarded = Column(Boolean, default=False)
    status = Column(String, default="completed")
    title = Column(String)
    overview = Column(Text)
    category = Column(String)
    action_items = Column(JSON, default=[])
    events = Column(JSON, default=[])
    photos = Column(JSON, default=[])
    apps_results = Column(JSON, default=[])
    plugins_results = Column(JSON, default=[])
    geolocation = Column(JSON)
    external_data = Column(JSON)
    language = Column(String, default="en")
    source = Column(String, default="friend")
    processing_memory_id = Column(String)
    visibility = Column(String, default="private")
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    memories = relationship("Memory", back_populates="conversation")


class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid"), index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    structured = Column(JSON)
    transcript_segments = Column(JSON)
    discarded = Column(Boolean, default=False)
    status = Column(String, default="completed")
    title = Column(String)
    overview = Column(Text)
    category = Column(String)
    action_items = Column(JSON, default=[])
    events = Column(JSON, default=[])
    photos = Column(JSON, default=[])
    apps_results = Column(JSON, default=[])
    plugins_results = Column(JSON, default=[])
    geolocation = Column(JSON)
    external_data = Column(JSON)
    language = Column(String, default="en")
    source = Column(String, default="friend")
    processing_memory_id = Column(String)
    visibility = Column(String, default="private")
    deleted = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="memories")
    conversation = relationship("Conversation", back_populates="memories")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid"), index=True)
    session_id = Column(String, index=True)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    sender = Column(String)  # 'human' or 'ai'
    type = Column(String, default='text')
    from_external_integration = Column(Boolean, default=False)
    plugin_id = Column(String)
    app_id = Column(String)


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid"), index=True)
    app_id = Column(String)
    description = Column(Text)
    title = Column(String)
    type = Column(String)  # 'text', 'audio', 'actionable'
    scopes = Column(ARRAY(String))
    token = Column(String)
    date_choices = Column(JSON)
    time_choices = Column(JSON)
    date_selected = Column(DateTime)
    time_selected = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid"), index=True)
    title = Column(String)
    description = Column(Text)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    
    uid = Column(String, ForeignKey("users.uid"), primary_key=True)
    token = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class AppUsageHistory(Base):
    __tablename__ = "app_usage_history"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid"), index=True)
    app_id = Column(String, ForeignKey("apps.id"), index=True)
    usage_type = Column(String) # Corresponds to UsageHistoryType Enum
    conversation_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship back to App
    app = relationship("App", back_populates="usage_history")


class Tester(Base):
    __tablename__ = "testers"
    
    uid = Column(String, primary_key=True, index=True)
    apps = Column(ARRAY(String), default=[])  # List of app IDs this tester has access to
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)