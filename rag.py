from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_postgres import PGVector
from sqlalchemy.ext.asyncio import create_async_engine
from typing import List, Optional
import logging
from db import get_vector_store
from config import settings
from email_utils import send_contact_email

logger = logging.getLogger(__name__)


async def ingest_documents(file_paths: list[str], clear: bool = False):
    try:
        vector_store = get_vector_store()
        if clear:
            await vector_store.adelete_collection()  # Async delete for efficiency
            logger.info("Cleared vector store collection before ingestion.")

        docs = []
        for path in file_paths:
            if path.endswith('.pdf'):
                loader = PyPDFLoader(path)
            elif path.endswith('.docx'):
                loader = Docx2txtLoader(path)
            elif path.endswith('.txt'):
                loader = TextLoader(path)
            else:
                raise ValueError(f"Unsupported file type: {path}")
            docs.extend(await loader.aload())  # Use async load for better perf

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        chunks = splitter.split_documents(docs)
        await vector_store.aadd_documents(chunks)  # Async add for concurrency
        logger.info(f"Ingested {len(chunks)} chunks from {len(file_paths)} files.")
    except ValueError as ve:
        logger.error(f"Ingestion value error: {ve}")
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise RuntimeError("Failed to ingest documents.") from e

@tool
async def retrieve_context(query: str) -> str:
    """Retrieve relevant context from the knowledge base to answer a query."""
    try:
        vector_store = get_vector_store()
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        docs = await retriever.ainvoke(query)
        serialized = "\n\n".join(doc.page_content for doc in docs)
        return serialized
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return "Failed to retrieve context."

@tool
async def send_contact_email_tool(name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, reason: Optional[str] = None, summary: str = "", decline_reason: Optional[str] = None) -> str:
    """Send an email with user contact details or decline reason and chat summary."""
    return await send_contact_email(name, email, phone, reason, summary, decline_reason)

def get_agent(session_store: dict):
    try:
        llm = ChatOpenAI(model=settings.llm_model, temperature=0.7, api_key=settings.openai_api_key)
        tools = [retrieve_context, send_contact_email_tool]

        system_prompt = (
            "You are an intelligent and helpful assistant part of the Exordium Networks team. "
            "Be professional, empathetic, and add a touch of humor when appropriate. "
            "Answer the user's question using ONLY the context from the retrieve_context tool. "
            "Ensure your response is Clear (easy to understand), Concise (to the point), "
            "Complete (covers all relevant details), Correct (factually accurate), "
            "and Courteous (polite and empathetic). Guide the user naturally. "
            "If no relevant info, politely say: 'I'm sorry, I don't have that information right now, but I'd be happy to help with something else.'\n\n"
            "To answer questions, if the latest user input references chat history, first reformulate it into a standalone query, "
            "then call retrieve_context with that query, then use the returned context to formulate your answer.\n\n"
            "For contact handling:\n"
            "- If the user expresses intent to contact us, collaborate, or similar, collect their name, email, phone number, and reason "
            "(skip reason if already shared in history). Inform them: 'Your details will be shared with the Exordium Networks team for follow-up.' "
            "Once collected, generate a concise chat summary, then call send_contact_email_tool with the details and summary.\n"
            "- If the conversation seems to be ending (e.g., user says 'thanks', 'bye', or no further questions) and contact details haven't been collected, "
            "politely ask: 'Before we wrap up, may I collect your name, email, and phone number? This will allow the Exordium Networks team to keep you updated on relevant news or opportunities.' "
            "If they provide, call the tool with details and summary (reason='future updates'). If they decline, ask courteously for the reason, "
            "then call the tool with the summary and decline_reason.\n"
            "Always confirm after sending: 'Your information has been shared with the team. Thank you!'"
        )

        agent = create_agent(llm, tools, system_prompt=system_prompt)
        return agent
    except Exception as e:
        logger.error(f"Agent setup error: {e}")
        raise RuntimeError("Failed to initialize agent.") from e


"""from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain  # Updated to latest langchain imports
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory  # Added for proper history
import logging
from db import get_vector_store
from config import settings

logger = logging.getLogger(__name__)

async def ingest_documents(file_paths: list[str], clear: bool = False):
    try:
        vector_store = get_vector_store()
        if clear:
            await vector_store.adelete_collection()  # Async delete for efficiency
            logger.info("Cleared vector store collection before ingestion.")

        docs = []
        for path in file_paths:
            if path.endswith('.pdf'):
                loader = PyPDFLoader(path)
            elif path.endswith('.docx'):
                loader = Docx2txtLoader(path)
            elif path.endswith('.txt'):
                loader = TextLoader(path)
            else:
                raise ValueError(f"Unsupported file type: {path}")
            docs.extend(await loader.aload())  # Use async load for better perf

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        chunks = splitter.split_documents(docs)
        await vector_store.aadd_documents(chunks)  # Async add for concurrency
        logger.info(f"Ingested {len(chunks)} chunks from {len(file_paths)} files.")
    except ValueError as ve:
        logger.error(f"Ingestion value error: {ve}")
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise RuntimeError("Failed to ingest documents.") from e

def get_rag_chain(session_store: dict):
    try:
        llm = ChatOpenAI(model=settings.llm_model, temperature=0.7, api_key=settings.openai_api_key)
        vector_store = get_vector_store()
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        # Contextualize query with history
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # Answer generation with 5Cs emphasis
        system_prompt = (
            "You are a helpful assistant for our company website. "
            "Answer the user's question using ONLY the retrieved context. "
            "Ensure your response is Clear (easy to understand), Concise (to the point), "
            "Complete (covers all relevant details), Correct (factually accurate), "
            "and Courteous (polite and empathetic). Guide the user naturally. "
            "If no relevant info, politely say: 'I'm sorry, I don't have that information right now, but I'd be happy to help with something else.'"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                ("system", "Context: {context}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # Add session memory with proper history object
        def get_session_history(session_id: str) -> BaseChatMessageHistory:
            if session_id not in session_store:
                session_store[session_id] = InMemoryChatMessageHistory()
            return session_store[session_id]

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        return conversational_rag_chain
    except Exception as e:
        logger.error(f"RAG chain error: {e}")
        raise RuntimeError("Failed to initialize RAG chain.") from e

"""