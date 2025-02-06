import os
import json
from lib.models import Environment

def set_env():
    # Check if config file exists
    if not os.path.exists("config.json"):
        raise FileNotFoundError("Config file not found! Please create a 'config.json' file.")

    # Read the config file
    with open("config.json", "r") as f:
        config = json.load(f)

    # Add them as environment variables
    for key, value in config.items():
        os.environ[key] = value

def get_env() -> Environment:
    # Read the config file
    with open("config.json", "r") as f:
        config = json.load(f)

    return config

def save_file(path: str, content: bytes):
    # First, save the file
    with open(path, "wb") as f:
        _ = f.write(content)