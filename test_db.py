import os
from urllib.parse import urlsplit

from dotenv import load_dotenv

from app.db import get_postgres_version

load_dotenv()


def safe_database_target(database_url: str | None) -> str:
    if not database_url:
        return "NOT SET"

    parsed = urlsplit(database_url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path.lstrip("/") or "unknown-database"
    return f"{host}{port}/{database}"


if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {safe_database_target(database_url)}")

    try:
        version = get_postgres_version()
        print(f"Connected! PostgreSQL version: {version}")
        print("Database connection successful!")
    except Exception as exc:
        print(f"Connection failed: {exc}")
        raise
