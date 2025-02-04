#!.env/bin/python3
# -*- coding: utf-8 -*-

from typing import Annotated
from contextlib import asynccontextmanager
import lib.helpers as helpers
from lib.models import sqlite_url, connect_args

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, create_engine

# Database configuration
engine = create_engine(sqlite_url, connect_args=connect_args)
def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    SQLModel.metadata.create_all(engine)
    helpers.setup()
    print("Setup complete!")
    yield
    print("ʕ·͡ᴥ·ʔ﻿ Goodbye!")

# Configure transport

# Configure pipeline

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
        "type": "welcome",
        "data": "Welcome to Codex!"
    }