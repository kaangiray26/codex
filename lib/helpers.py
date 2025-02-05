import os
import json
from sqlmodel import SQLModel
from lib.models import Environment

def get_env() -> Environment:
    # Read the config file
    with open("config.json", "r") as f:
        config = json.load(f)

    return config

def parse_config():
    # Check if config file exists
    if not os.path.exists("config.json"):
        raise FileNotFoundError("Config file not found! Please create a 'config.json' file.")

    # Read the config file
    with open("config.json", "r") as f:
        config = json.load(f)

    # Add them as environment variables
    for key, value in config.items():
        os.environ[key] = value

def save_file(path: str, content: bytes):
    with open(path, "wb") as f:
        _ = f.write(content)

def startup(engine):
    SQLModel.metadata.create_all(engine)

    # Parse the config file
    parse_config()

    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)

def shutdown(processes):
    for process in processes.values():
        process.terminate()
        process.wait()
    print("ʕ·͡ᴥ·ʔ﻿ Goodbye!")