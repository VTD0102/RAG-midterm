"""
LangChain RAG Agent with:
- Hybrid search (semantic + BM25)
- Conversation memory (SQLite-backed)
- Streaming support via async generators
- Source citations in responses
"""
import asyncio
from typing import AsyncGenerator, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

from app.config import settings
from app.vectorstore import get_vectorstore, get_embeddings
from app.memory import get_history, add_message, ensure_session
from app.schemas import SourceDocument

# ── System Prompt ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Bạn là một trợ lý AI thông minh có khả năng trả lời câu hỏi dựa trên tài liệu được cung cấp.

Hướng dẫn:
1. Trả lời dựa trên các đoạn văn bản trong phần "Ngữ cảnh" bên dưới
2. Nếu thông tin không có trong ngữ cảnh, hãy nói rõ là bạn không tìm thấy thông tin liên quan
3. Trích dẫn nguồn khi cần thiết
4. Trả lời bằng ngôn ngữ của câu hỏi (tiếng Việt hoặc tiếng Anh)
5. Nếu câu hỏi là casual/chào hỏi, trả lời tự nhiên mà không cần ngữ cảnh

Ngữ cảnh từ tài liệu:
{context}
"""

# ── LLM ───────────────────────────────────────────────────────────────────
def get_llm(streaming: bool = False) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        streaming=streaming,
        temperature=0.3,
    )


# ── In-memory BM25 document store (lazy populated) ────────────────────────
_bm25_documents: List[Document] = []


def get_hybrid_retriever(query: str) -> EnsembleRetriever:
    """Build a hybrid retriever combining Pinecone (semantic) + BM25 (keyword)."""
    vectorstore = get_vectorstore()
    dense_retriever = vectorstore.as_retriever(
        search_kwargs={"k": settings.retriever_top_k + 3}
    )

    if _bm25_documents:
        bm25_retriever = BM25Retriever.from_documents(_bm25_documents)
        bm25_retriever.k = settings.retriever_top_k + 3
        return EnsembleRetriever(
            retrievers=[bm25_retriever, dense_retriever],
            weights=[settings.bm25_weight, 1 - settings.bm25_weight],
        )

    return dense_retriever  # type: ignore


def update_bm25_store(new_docs: List[Document]) -> None:
    """Append newly ingested documents to the in-memory BM25 index."""
    _bm25_documents.extend(new_docs)


# ── Core RAG Logic ────────────────────────────────────────────────────────

async def retrieve_context(query: str) -> tuple[str, List[SourceDocument]]:
    """Retrieve relevant documents and format context string + source list."""
    retriever = get_hybrid_retriever(query)
    docs: List[Document] = await retriever.ainvoke(query)

    # Deduplicate by content
    seen = set()
    unique_docs = []
    for doc in docs:
        key = doc.page_content[:200]
        if key not in seen:
            seen.add(key)
            unique_docs.append(doc)

    unique_docs = unique_docs[: settings.retriever_top_k]

    # Build context string
    context_parts = []
    for i, doc in enumerate(unique_docs):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "")
        page_info = f" (trang {page + 1})" if page != "" else ""
        context_parts.append(f"[{i+1}] Nguồn: {source}{page_info}\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts) if context_parts else "Không có ngữ cảnh."

    # Build source list
    sources = [
        SourceDocument(
            content=doc.page_content[:300],
            source=doc.metadata.get("source", "unknown"),
            page=doc.metadata.get("page"),
        )
        for doc in unique_docs
    ]

    return context, sources


async def chat(
    message: str,
    session_id: str,
) -> tuple[str, List[SourceDocument]]:
    """
    Non-streaming chat: returns (answer, sources).
    """
    await ensure_session(session_id, first_message=message)
    history = await get_history(session_id)
    context, sources = await retrieve_context(message)

    llm = get_llm(streaming=False)
    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]
    messages.extend(history)
    messages.append(HumanMessage(content=message))

    response = await llm.ainvoke(messages)
    answer: str = response.content

    # Persist to memory
    await add_message(session_id, "human", message)
    await add_message(session_id, "ai", answer)

    return answer, sources


async def chat_stream(
    message: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """
    Streaming chat: yields text tokens, then a JSON sources block.
    SSE format handled by FastAPI endpoint.
    """
    await ensure_session(session_id, first_message=message)
    history = await get_history(session_id)
    context, sources = await retrieve_context(message)

    llm = get_llm(streaming=True)
    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]
    messages.extend(history)
    messages.append(HumanMessage(content=message))

    full_answer = ""
    async for chunk in llm.astream(messages):
        token = chunk.content
        if token:
            full_answer += token
            yield token

    # Persist to memory after streaming completes
    await add_message(session_id, "human", message)
    await add_message(session_id, "ai", full_answer)

    # Yield sources as a special sentinel JSON
    import json
    yield "\n\n__SOURCES__" + json.dumps(
        [s.model_dump() for s in sources]
    )
