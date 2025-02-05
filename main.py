#!.env/bin/python3
# -*- coding: utf-8 -*-

import os
import subprocess
from uuid import uuid4
from typing import Annotated, Any, Dict
from contextlib import asynccontextmanager
from pydantic import ValidationError
import lib.helpers as helpers
from lib.models import sqlite_url, connect_args, Documents
from lib.manager import ConnectionManager

# FastAPI
from fastapi import FastAPI, Request, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, create_engine

# Database configuration
engine = create_engine(sqlite_url, connect_args=connect_args)
def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]

# Global variables
processes = dict()
manager = ConnectionManager()

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    helpers.startup(engine)
    yield
    helpers.shutdown(processes)

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
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
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

    # Set the document
    manager.document = document

    # Return the document ID
    return {
        "success": True,
        "data": {
            "document": document
        }
    }

@app.post("/connect")
async def rtvi_connect(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Dict[Any, Any]:
    # Get the room URL and token
    room_url, token = await manager.create_room_and_token()

    # Spawn a new bot for the room
    try:
        proc = subprocess.Popen(
            [f"python3 -m lib.bots.default -u {room_url} -t {token}"],
            shell=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        # Add the process to the list
        processes[proc.pid] = proc
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to process!")

    # Return the room URL and token
    return {"room_url": room_url, "token": token}