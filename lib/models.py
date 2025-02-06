from typing import TypedDict
from datetime import datetime
from sqlmodel import SQLModel, Field

# SQLModel configuration
sqlite_file_name = "codex.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}

class Documents(SQLModel, table=True):
    id: str = Field(
        primary_key=True,
    )
    filename: str = Field(
        ...,
        description="The name of the document",
    )
    content_type: str = Field(
        ...,
        description="The MIME type of the document",
    )
    path: str = Field(
        ...,
        description="The path to the document in the filesystem",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="The date and time the document was created",
    )

class Environment(TypedDict):
    OPENAI_API_KEY: str
    DEEPGRAM_API_KEY: str
    ELEVENLABS_API_KEY: str
    DAILY_API_KEY: str
    DAILY_ROOM_URL: str