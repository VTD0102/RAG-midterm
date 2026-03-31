"""
LangChain RAG Agent with:
- Hybrid search (semantic + BM25)
- Conversation memory (SQLite-backed)
- Streaming support via async generators
- Source citations in responses
"""
import asyncio
from typing import AsyncGenerator, List

from langchain_openai import ChatOpenAI
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
SYSTEM_PROMPT = """Bạn là một trợ lý AI thông minh, có trách nhiệm cung cấp câu trả lời CHI TIẾT và ĐẦY ĐỦ dựa trên tài liệu được cung cấp.

Hướng dẫn:
1. **Phân tích kỹ lưỡng**: Đừng chỉ đưa ra câu trả lời ngắn gọn. Hãy giải thích các khía cạnh liên quan tìm thấy trong ngữ cảnh.
2. **Cấu trúc rõ ràng**: Sử dụng Markdown (bullet points, tiêu đề, in đậm) để làm câu trả lời dễ đọc và chuyên nghiệp.
3. **Chỉ dùng ngữ cảnh**: Chỉ sử dụng thông tin trong phần "Ngữ cảnh" bên dưới. Nếu không có thông tin, hãy trả lời: "Tôi không tìm thấy thông tin liên quan trong tài liệu được cung cấp." Tuyệt đối không tự bịa ra thông tin.
4. **Trích dẫn nguồn**: Luôn trích dẫn nguồn cụ thể ở cuối mỗi ý hoặc cuối câu trả lời (ví dụ: [Nguồn: đoạn X]).
5. **Ngôn ngữ**: Trả lời bằng ngôn ngữ của người dùng (Tiếng Việt hoặc Tiếng Anh).
6. **Hội thoại**: Nếu là câu hỏi chào hỏi hoặc xã giao, hãy trả lời một cách thân thiện và tự nhiên.

Ngữ cảnh:
{context}
"""

# ── Condense Question Prompt (Query Rewriting) ─────────────────────────────
CONDENSE_QUESTION_PROMPT = """Dựa vào lịch sử hội thoại và câu hỏi mới nhất từ người dùng, hãy tạo ra một câu hỏi ĐỘC LẬP (standalone question) có đầy đủ ngữ cảnh để dùng cho việc tìm kiếm tài liệu.

Yêu cầu:
1. Nếu câu hỏi đã đủ ý, hãy giữ nguyên.
2. Nếu là câu chào hỏi hoặc không liên quan đến tìm kiếm, hãy giữ nguyên.
3. KHÔNG trả lời câu hỏi, chỉ viết lại câu hỏi dưới dạng một câu truy vấn tìm kiếm hiệu quả.
4. Giữ nguyên ngôn ngữ gốc của người dùng.

Lịch sử hội thoại:
{chat_history}

Câu hỏi mới: {question}
Câu hỏi độc lập:"""

# ── Reranking Prompt ──────────────────────────────────────────────────────
RERANK_PROMPT = """Bạn là một chuyên gia thẩm định tài liệu. Dưới đây là câu hỏi của người dùng và danh sách các đoạn văn bản tiềm năng (đánh số từ 1-20).
Nhiệm vụ của bạn: Chọn ra tối đa {top_k} ID của các đoạn văn bản LIÊN QUAN NHẤT để trả lời câu hỏi.

Câu hỏi: {question}

Danh sách tài liệu:
{documents}

Yêu cầu:
1. Chỉ trả về các con số ID, ngăn cách bởi dấu phẩy (ví dụ: 1, 4, 7).
2. Sắp xếp theo thứ tự độ liên quan giảm dần.
3. Không giải thích gì thêm.

ID các tài liệu tốt nhất:"""

# ── LLM ───────────────────────────────────────────────────────────────────
def get_llm(streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        streaming=streaming,
        temperature=0.4,
    )


# ── In-memory BM25 document store (lazy populated) ────────────────────────
_bm25_documents: List[Document] = []


def get_hybrid_retriever(query: str, k: int = 10) -> EnsembleRetriever:
    """Build a hybrid retriever combining Pinecone (semantic) + BM25 (keyword)."""
    vectorstore = get_vectorstore()
    dense_retriever = vectorstore.as_retriever(
        search_kwargs={"k": k}
    )

    if _bm25_documents:
        bm25_retriever = BM25Retriever.from_documents(_bm25_documents)
        bm25_retriever.k = k
        return EnsembleRetriever(
            retrievers=[bm25_retriever, dense_retriever],
            weights=[settings.bm25_weight, 1 - settings.bm25_weight],
        )

    return dense_retriever  # type: ignore


def update_bm25_store(new_docs: List[Document]) -> None:
    """Append newly ingested documents to the in-memory BM25 index."""
    _bm25_documents.extend(new_docs)


# ── Core RAG Logic ────────────────────────────────────────────────────────

async def retrieve_context(query: str, original_query: str = "") -> tuple[str, List[SourceDocument]]:
    """Retrieve relevant documents, rerank them, and format context string + source list."""
    # Use the original query for reranking if provided, otherwise use the search query
    rank_query = original_query or query
    
    # Fetch more candidates for reranking (e.g. 20)
    retriever = get_hybrid_retriever(query, k=20)
    docs: List[Document] = await retriever.ainvoke(query)

    # Deduplicate by content
    seen = set()
    unique_candidates = []
    for doc in docs:
        key = doc.page_content[:200]
        if key not in seen:
            seen.add(key)
            unique_candidates.append(doc)

    # ── Reranking ──
    # Pick the top_k from the candidates using LLM
    unique_docs = await rerank_documents(rank_query, unique_candidates, top_k=settings.retriever_top_k)

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


async def rerank_documents(query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
    """Use LLM to rerank documents and pick the top_k best candidates."""
    if not docs:
        return []
    if len(docs) <= top_k:
        return docs

    # Format documents for the prompt
    docs_str = ""
    for i, doc in enumerate(docs[:20]):  # Limit to 20 candidates for reranking
        docs_str += f"ID {i+1}: {doc.page_content[:500]}\n---\n"

    llm = get_llm(streaming=False)
    prompt = RERANK_PROMPT.format(
        question=query,
        documents=docs_str,
        top_k=top_k
    )

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        
        # Parse IDs from response (e.g. "1, 4, 7")
        import re
        ids = [int(i) for i in re.findall(r'\d+', content)]
        
        reranked_docs = []
        seen_indices = set()
        for idx in ids:
            actual_idx = idx - 1
            if 0 <= actual_idx < len(docs) and actual_idx not in seen_indices:
                reranked_docs.append(docs[actual_idx])
                seen_indices.add(actual_idx)
        
        # Fallback if parsing fails or returns nothing
        if not reranked_docs:
            return docs[:top_k]
            
        return reranked_docs[:top_k]
    except Exception as e:
        print(f"Reranking failed: {e}")
        return docs[:top_k]


async def rewrite_query(message: str, history: List) -> str:
    """Rewrite the user message into a standalone search query if context exists."""
    if not history:
        return message

    # Format chat history for the prompt
    history_str = ""
    for msg in history[-5:]:  # Only look at last 5 messages for context
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        history_str += f"{role}: {msg.content}\n"

    llm = get_llm(streaming=False)
    prompt = CONDENSE_QUESTION_PROMPT.format(
        chat_history=history_str, 
        question=message
    )
    
    response = await llm.ainvoke(prompt)
    rewritten = response.content.strip()
    
    # Clean up any AI prefixing if necessary
    if rewritten.lower().startswith("câu hỏi độc lập:"):
        rewritten = rewritten[len("câu hỏi độc lập:"):].strip()
        
    return rewritten


async def chat(
    message: str,
    session_id: str,
) -> tuple[str, List[SourceDocument]]:
    """
    Non-streaming chat: returns (answer, sources).
    """
    await ensure_session(session_id, first_message=message)
    history = await get_history(session_id)

    # ── Query Rewriting ──
    search_query = await rewrite_query(message, history)
    context, sources = await retrieve_context(search_query, original_query=message)

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

    # ── Query Rewriting ──
    search_query = await rewrite_query(message, history)
    context, sources = await retrieve_context(search_query, original_query=message)

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
