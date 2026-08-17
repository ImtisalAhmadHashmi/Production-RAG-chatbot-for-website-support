from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import uuid
import logging
from typing import List
import os
from rag import get_agent, ingest_documents
from db import get_vector_store
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

app = FastAPI(title="RAG Chatbot API")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

session_store: dict[str, InMemoryChatMessageHistory] = {}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY = os.getenv("API_KEY", "sogqgqjAumSW_iSFkbuNElE0BCuhDXuhSTUefntR9fo")

def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

class ChatRequest(BaseModel):
    query: str
    session_id: str = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _=Depends(get_api_key)):
    try:
        if not request.session_id:
            request.session_id = str(uuid.uuid4())

        agent = get_agent(session_store)
        history = session_store.get(request.session_id, InMemoryChatMessageHistory())

        input_message = HumanMessage(content=request.query)
        messages = history.messages + [input_message]

        response = await agent.ainvoke({"messages": messages})

        # Update history with the full new state
        history.messages = response["messages"]

        # Extract final AI response
        final_answer = next((m.content for m in reversed(response["messages"]) if isinstance(m, AIMessage)), "No response generated.")

        session_store[request.session_id] = history

        return ChatResponse(answer=final_answer, session_id=request.session_id)
    except RuntimeError as re:
        logger.error(f"Chat runtime error: {re}")
        raise HTTPException(status_code=500, detail="Chat processing failed") from re
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@app.post("/ingest")
async def ingest(
    files: List[UploadFile] = File(...),
    clear: bool = Query(False, description="Clear vector store before ingestion"),
    _=Depends(get_api_key)
):
    try:
        file_paths = []
        os.makedirs("data", exist_ok=True)
        for file in files:
            path = f"data/{file.filename}"
            with open(path, "wb") as f:
                f.write(await file.read())
            file_paths.append(path)
        await ingest_documents(file_paths, clear=clear)  # Async call
        return {"status": "Ingestion successful", "files_processed": len(file_paths)}
    except ValueError as ve:
        logger.error(f"Ingestion value error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except RuntimeError as re:
        logger.error(f"Ingestion runtime error: {re}")
        raise HTTPException(status_code=500, detail="Ingestion failed") from re
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Ingestion failed") from e

@app.delete("/clear_vectorstore")
async def clear_vectorstore(_=Depends(get_api_key)):
    try:
        vector_store = get_vector_store()
        await vector_store.adelete_collection()  # Async delete
        logger.info("Vector store collection cleared.")
        return {"status": "Vector store cleared successfully"}
    except Exception as e:
        logger.error(f"Clear vector store error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear vector store") from e



"""from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import uuid
import logging
from typing import List
import os
from rag import get_rag_chain, ingest_documents
from db import get_vector_store  # For clear endpoint
from langchain_core.chat_history import InMemoryChatMessageHistory

app = FastAPI(title="RAG Chatbot API")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# In-memory session store (replace with Redis for production scalability)
session_store: dict[str, InMemoryChatMessageHistory] = {}  # Typed for clarity

# API Key for auth (set via env in production: os.getenv("API_KEY"))
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY = os.getenv("API_KEY", "sogqgqjAumSW_iSFkbuNElE0BCuhDXuhSTUefntR9fo")  # Default for dev

def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

class ChatRequest(BaseModel):
    query: str
    session_id: str = None  # Optional; generate if not provided

class ChatResponse(BaseModel):
    answer: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _=Depends(get_api_key)):
    try:
        if not request.session_id:
            request.session_id = str(uuid.uuid4())

        chain = get_rag_chain(session_store)
        response = await chain.ainvoke(  # Async for low latency
            {"input": request.query},
            config={"configurable": {"session_id": request.session_id}}
        )
        return ChatResponse(answer=response["answer"], session_id=request.session_id)
    except RuntimeError as re:
        logger.error(f"Chat runtime error: {re}")
        raise HTTPException(status_code=500, detail="Chat processing failed") from re
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/ingest")
async def ingest(
    files: List[UploadFile] = File(...),
    clear: bool = Query(False, description="Clear vector store before ingestion"),
    _=Depends(get_api_key)
):
    try:
        file_paths = []
        os.makedirs("data", exist_ok=True)
        for file in files:
            path = f"data/{file.filename}"
            with open(path, "wb") as f:
                f.write(await file.read())
            file_paths.append(path)
        await ingest_documents(file_paths, clear=clear)  # Async call
        return {"status": "Ingestion successful", "files_processed": len(file_paths)}
    except ValueError as ve:
        logger.error(f"Ingestion value error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except RuntimeError as re:
        logger.error(f"Ingestion runtime error: {re}")
        raise HTTPException(status_code=500, detail="Ingestion failed") from re
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Ingestion failed") from e

@app.delete("/clear_vectorstore")
async def clear_vectorstore(_=Depends(get_api_key)):
    try:
        vector_store = get_vector_store()
        await vector_store.adelete_collection()  # Async delete
        logger.info("Vector store collection cleared.")
        return {"status": "Vector store cleared successfully"}
    except Exception as e:
        logger.error(f"Clear vector store error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear vector store") from e

"""