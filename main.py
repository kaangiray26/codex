#!.env/bin/python3
# -*- coding: utf-8 -*-

import os
from uuid import uuid4
from typing import Annotated
from contextlib import asynccontextmanager
from pydantic import ValidationError
import lib.helpers as helpers
from lib.models import sqlite_url, connect_args, Documents
from lib.manager import ConnectionManager

# FastAPI
from fastapi import FastAPI, WebSocket, Depends, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, create_engine

# Pipecat
from pipecat.pipeline.pipeline import Pipeline
from pipecat.serializers.protobuf import ProtobufFrameSerializer

# Database configuration
engine = create_engine(sqlite_url, connect_args=connect_args)
def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]

# ConnectionManager for handling websockets
manager = ConnectionManager()

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    SQLModel.metadata.create_all(engine)
    helpers.setup()
    print("Setup complete!")
    yield
    print("ʕ·͡ᴥ·ʔ﻿ Goodbye!")

# Initialize the application
app = FastAPI(lifespan=lifespan)

# Configure CORS,
# so that we can actually make requests :D
origins = [
    "http://localhost",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def index():
    return {
        "success": True,
        "data": {
            "Welcome to Codex!"
        }
    }

@app.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    session: SessionDep,
    file: UploadFile = File(...),
):
    # Check if we have a file
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Create an UUID for the document
    document_id = uuid4()

    # Validate the document
    try:
        document = Documents(
            id=document_id,
            name=file.filename,
            path=os.path.join("uploads", str(document_id)),
        )
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid document.")

    # Add the document object to the database
    session.add(document)
    session.commit()
    session.refresh(document)

    # Save the file in the background
    content = await file.read()
    background_tasks.add_task(helpers.save_file, document.path, content)

    # Return the document ID
    return {
        "success": True,
        "data": {
            "document": document
        }
    }

# Websocket
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):
    # Configure transport
    transport = await manager.connect(websocket)

    # Create a pipeline
    pipeline = Pipeline([
        transport.input(),    # Handle incoming audio
        stt,                  # Speech-to-text
        llm,                  # Language model
        tts,                  # Text-to-speech
        transport.output()    # Handle outgoing audio
    ])