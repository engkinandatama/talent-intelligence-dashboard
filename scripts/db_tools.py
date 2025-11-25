from sqlalchemy import create_engine, text
import pandas as pd

def get_engine_manual():
    secrets = {}
    try:
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    secrets[key] = value
    except FileNotFoundError:
        print("Secrets file not found.")
        return None
    
    DB_USER = secrets.get("DB_USER")
    DB_PASS = secrets.get("DB_PASS")
    DB_HOST = secrets.get("DB_HOST")
    DB_PORT = secrets.get("DB_PORT")
    DB_NAME = secrets.get("DB_NAME")

    if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
        print("Missing DB config in secrets.")
        return None

    url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)
