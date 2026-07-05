import uuid
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)

class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    security_events: list["SecurityEvent"] = Relationship(back_populates="user", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SecurityEvent(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    event_type: str
    severity: Severity
    user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
    )
    user: User | None = Relationship(
        back_populates="security_events"
    )
    ip: str | None = None
    source: str = "api"
    event_data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

class SecurityEventCreate(SQLModel):
    event_type: str
    severity: Severity
    ip: str | None = None
    source: str = "api"
    event_data: dict = Field(default_factory=dict)


class SecurityEventPublic(SQLModel):
    id: uuid.UUID
    event_type: str
    severity: Severity
    user_id: uuid.UUID | None
    ip: str | None
    source: str
    event_data: dict
    created_at: datetime


class SecurityEventsPublic(SQLModel):
    data: list[SecurityEventPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str

# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

class OutboxEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    event_type: str
    payload: str

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    processed: bool = False