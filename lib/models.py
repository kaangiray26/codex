from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

# SQLModel configuration
sqlite_file_name = "codex.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}

class Documents(SQLModel, table=True):
    id: UUID = Field(
        primary_key=True,
        default_factory=uuid4,
    )
    name: str = Field(
        ...,
        description="The name of the document",
    )
    path: str = Field(
        ...,
        description="The path to the document in the filesystem",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="The date and time the document was created",
    )