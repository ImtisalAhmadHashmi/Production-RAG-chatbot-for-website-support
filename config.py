import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus
from typing import Optional

load_dotenv(override=True)

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    database_url: str = f"postgresql+psycopg://{POSTGRES_USER}:{quote_plus(POSTGRES_PASSWORD)}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-5-nano"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: str = "rag_collection"
    sender_email: str = os.getenv("SENDER_EMAIL")
    sender_password: str = os.getenv("SENDER_PASSWORD")
    recipient_email: str = os.getenv("RECIPIENT_EMAIL")
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = os.getenv("SMTP_PORT", 587)

settings = Settings()






"""import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus  # Improved for URL encoding

load_dotenv(override=True)

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    database_url: str = f"postgresql+psycopg://{POSTGRES_USER}:{quote_plus(POSTGRES_PASSWORD)}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-5-nano"  # Assuming available in 2026; fallback to gpt-4o-mini if needed
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: str = "rag_collection"

settings = Settings()

"""