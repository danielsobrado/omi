# backend/database/postgres/models.py
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, Text, ForeignKey, JSON, Integer,
    func, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid
from .client import Base


class User(Base):
    __tablename__ = "users"

    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    display_name = Column(String)
    fcm_token = Column(String, nullable=True)
    time_zone = Column(String, nullable=True, default='UTC')
    store_recording_permission = Column(Boolean, default=False)
    stripe_account_id = Column(String, nullable=True)
    paypal_details = Column(JSON, nullable=True)
    default_payment_method = Column(String, nullable=True)
    language = Column(String, nullable=True)
    data_protection_level = Column(String, default='standard')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    apps = relationship("App", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    people = relationship("Person", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Person(Base):
    __tablename__ = "people"
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    user = relationship("User", back_populates="people")


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    value = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="ratings")


class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, index=True)
    app_id = Column(String, ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)
    hashed = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    app = relationship("App")


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
    usage_history = relationship("AppUsageHistory", back_populates="app", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="app", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    structured = Column(JSON)
    transcript_segments = Column(JSON) # Can store encrypted/compressed data
    transcript_segments_compressed = Column(Boolean, default=False)
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
    data_protection_level = Column(String, default='standard')

    # Relationships
    user = relationship("User", back_populates="conversations")
    memories = relationship("Memory", back_populates="conversation", cascade="all, delete-orphan")
    photos_rel = relationship("ConversationPhoto", back_populates="conversation", cascade="all, delete-orphan")
    postprocessing_results = relationship("PostprocessingResult", back_populates="conversation", cascade="all, delete-orphan")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    structured = Column(JSON)
    content = Column(Text, nullable=True) # For encrypted content
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
    data_protection_level = Column(String, default='standard')
    reviewed = Column(Boolean, default=False)
    user_review = Column(Boolean, nullable=True)
    edited = Column(Boolean, default=False)
    scoring = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="memories")
    conversation = relationship("Conversation", back_populates="memories")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    session_id = Column(String, index=True)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    sender = Column(String)
    type = Column(String, default='text')
    from_external_integration = Column(Boolean, default=False)
    plugin_id = Column(String)
    app_id = Column(String)
    reported = Column(Boolean, default=False)
    data_protection_level = Column(String, default='standard')
    memories_id = Column(ARRAY(String), default=[])
    files_id = Column(ARRAY(String), default=[])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    app_id = Column(String)
    description = Column(Text)
    title = Column(String)
    type = Column(String)
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
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    title = Column(String)
    description = Column(Text)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    action = Column(String, nullable=True)
    request_id = Column(String, nullable=True)


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), primary_key=True)
    token = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class AppUsageHistory(Base):
    __tablename__ = "app_usage_history"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), index=True)
    app_id = Column(String, ForeignKey("apps.id", ondelete="CASCADE"), index=True)
    usage_type = Column(String)
    conversation_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    app = relationship("App", back_populates="usage_history")


class Tester(Base):
    __tablename__ = "testers"

    uid = Column(String, primary_key=True, index=True)
    apps = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VectorStore(Base):
    __tablename__ = "vector_store"
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    embedding = Column(Vector(3072)) # For text-embedding-3-large
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class File(Base):
    __tablename__ = "files"
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String)
    type = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="files")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    app_id = Column(String, ForeignKey("apps.id"), nullable=True)
    message_ids = Column(ARRAY(String), default=[])
    file_ids = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="chat_sessions")


class ConversationPhoto(Base):
    __tablename__ = "conversation_photos"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String)
    timestamp = Column(DateTime)
    conversation = relationship("Conversation", back_populates="photos_rel")


class PostprocessingResult(Base):
    __tablename__ = "postprocessing_results"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String, nullable=False)
    result_type = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="postprocessing_results")