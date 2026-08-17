from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from config import settings


logger = logging.getLogger(__name__)

def get_vector_store():
    try:
        embeddings = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
        engine = create_async_engine(settings.database_url)
        vector_store = PGVector(
            connection=engine,
            embeddings=embeddings,
            collection_name=settings.collection_name,
            use_jsonb=True,
            async_mode=True  # Enable async for low-latency concurrent ops
        )
        return vector_store
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        raise RuntimeError("Failed to connect to vector database.") from e
    except Exception as e:
        logger.error(f"Unexpected error in vector store setup: {e}")
        raise RuntimeError("Failed to initialize vector store.") from e


