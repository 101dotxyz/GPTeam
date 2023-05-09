import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, REAL, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy_utils import VectorType

Base = declarative_base()

# Creating enum types
MemoryType = Enum("reflection", "observation", name="memory_type")
EventType = Enum("non_message", "message", name="event_type")
PlanStatus = Enum("in_progress", "todo", "done", name="plan_status")

# Association table for agents and ordered plans
agent_ordered_plans = Table(
    "agent_ordered_plans",
    Base.metadata,
    Column("agent_id", String, ForeignKey("agents.id"), primary_key=True),
    Column("plan_id", String, ForeignKey("plans.id"), primary_key=True),
)


# Defining models
class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()), nullable=False)
    full_name = Column(Text)
    private_bio = Column(Text)
    public_bio = Column(Text)
    authorized_tools = Column(ARRAY(Text))
    directives = Column(ARRAY(Text))
    world_id = Column(String, ForeignKey("worlds.id", ondelete="CASCADE"))
    last_checked_events = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    ordered_plan_ids = relationship(
        "Plan", secondary=agent_ordered_plans, back_populates="assigned_agents"
    )
    location_id = Column(String, ForeignKey("locations.id"))
    discord_bot_token = Column(Text)


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"))
    type = Column(MemoryType)
    description = Column(Text)
    related_memory_ids = Column(ARRAY(String))
    embedding = Column(String)  # using string type instead of vector
    importance = Column(SmallInteger)
    last_accessed = Column(TIMESTAMP(timezone=True))


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"))
    description = Column(Text)
    location_id = Column(String, ForeignKey("locations.id"))
    max_duration_hrs = Column(REAL)
    stop_condition = Column(Text)
    completed_at = Column(TIMESTAMP(timezone=True))
    scratchpad = Column(JSONB)
    status = Column(PlanStatus, nullable=False, server_default="todo")
    related_event_id = Column(String, ForeignKey("events.id"))
    assigned_agents = relationship(
        "Agent", secondary=agent_ordered_plans, back_populates="ordered_plan_ids"
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"))
    timestamp = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    type = Column(EventType)
    subtype = Column(Text)
    description = Column(Text)
    location_id = Column(String, ForeignKey("locations.id", ondelete="CASCADE"))
    witness_ids = Column(ARRAY(String))
    metadata = Column(JSONB)


class Location(Base):
    __tablename__ = "locations"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()), nullable=False)
    world_id = Column(String, ForeignKey("worlds.id"))
    name = Column(Text)
    available_tools = Column(ARRAY(Text))
    description = Column(Text)
    channel_id = Column(Integer)
    allowed_agent_ids = Column(ARRAY(String))


class World(Base):
    __tablename__ = "worlds"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()), nullable=False)
    name = Column(Text)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"))
    title = Column(Text)
    normalized_title = Column(Text)
    content = Column(Text)
    embedding = Column(String)  # using string type instead of vector

    __table_args__ = (
        UniqueConstraint(
            "agent_id", "normalized_title", name="_agent_normalized_title_uc"
        ),
    )


def match_documents(query_embedding, match_threshold, match_count):
    query = text(
        """
        SELECT
            "public"."Documents".id,
            "public"."Documents"."created_at",
            "public"."Documents"."agent_id",
            "public"."Documents"."title",
            "public"."Documents"."normalized_title",
            "public"."Documents".content,
            1 - similarity("public"."Documents".embedding, :query_embedding) as similarity
        FROM "public"."Documents"
        WHERE 1 - similarity("public"."Documents".embedding, :query_embedding) > :match_threshold
        ORDER BY similarity DESC
        LIMIT :match_count
    """
    )
    params = {
        "query_embedding": query_embedding,
        "match_threshold": match_threshold,
        "match_count": match_count,
    }
    result = engine.execute(query, params)
    return [
        {
            "id": row[0],
            "created_at": row[1],
            "agent_id": row[2],
            "title": row[3],
            "normalized_title": row[4],
            "content": row[5],
            "similarity": row[6],
        }
        for row in result
    ]
