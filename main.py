#!.env/bin/python3
# -*- coding: utf-8 -*-

import os
import subprocess
from hashlib import sha256
from lib.index import LlamaIndex
from typing import Annotated, Any, Dict
from contextlib import asynccontextmanager
from pydantic import ValidationError
import lib.helpers as helpers
from lib.models import sqlite_url, connect_args, Documents
from lib.manager import ConnectionManager

# FastAPI
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, create_engine
from fastapi import FastAPI, Request, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Database configuration
engine = create_engine(sqlite_url, connect_args=connect_args)
def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]

# Tools
helpers.set_env()
llama_index = LlamaIndex()
manager = ConnectionManager()

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    os.makedirs("uploads", exist_ok=True)
    yield
    manager.terminate_processes()
    print("ʕ·͡ᴥ·ʔ﻿ Goodbye!")

# Initialize the application
app = FastAPI(lifespan=lifespan)

# Serve the static files
app.mount("/app", StaticFiles(directory="dist", html=True), name="app")

# Configure CORS,
origins = [
    "http://localhost",
    "http://localhost:8000",
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
@app.get("/check")
async def check():
    return {"status": "ok"}

@app.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    session: SessionDep,
    file: UploadFile = File(...),
):
    # Check if we have a file
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Save the file in the background
    content = await file.read()

    # Calculate the hash of the content
    hash = sha256(content).hexdigest()

    # Validate the document
    try:
        document = Documents(
            id=hash,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            path=os.path.join("uploads", hash),
        )
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid document.")

    # Add the document object to the database
    try:
        session.add(document)
        session.commit()
        session.refresh(document)

        # Save the file in the background
        background_tasks.add_task(helpers.save_file, document.path, content)
        background_tasks.add_task(llama_index.add_document_to_index, document.id)
    except IntegrityError:
        pass

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
            [f"python3 -m lib.bots.default -u {room_url} -t {token} -d {manager.document.id}"],
            shell=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        # Add the process to the list
        manager.add_process(proc.pid, proc)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to process!")

    # Return the room URL and token
    return {"room_url": room_url, "token": token}

if __name__ == "__main__":
    import shutil
    import argparse
    parser = argparse.ArgumentParser(description="Codex CLI")
    parser.add_argument("command", type=str, help="The command to run", choices=["reset"])

    args = parser.parse_args()

    # Handle args
    match args.command:
        case "reset":
            print("Resetting...")
            os.remove("codex.db")
            shutil.rmtree("uploads", ignore_errors=True)
            shutil.rmtree("storage", ignore_errors=True)
            print("Done!")