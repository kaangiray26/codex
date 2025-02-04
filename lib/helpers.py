import os
import json

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

def setup():
    # Parse the config file
    parse_config()

    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)

def save_file(path: str, content: bytes):
    with open(path, "wb") as f:
        _ = f.write(content)