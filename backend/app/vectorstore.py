"""
Pinecone vector store setup with Gemini embeddings.
Supports initialization and hybrid search (semantic + BM25).
"""
import os
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """Returns a cached OpenAI/OpenRouter embedding model."""
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )


@lru_cache(maxsize=1)
def get_pinecone_client() -> Pinecone:
    """Returns a cached Pinecone client."""
    return Pinecone(api_key=settings.pinecone_api_key)


def ensure_index_exists(pc: Pinecone) -> None:
    """Create Pinecone index if it doesn't exist yet."""
    existing = [idx.name for idx in pc.list_indexes()]
    if settings.pinecone_index_name not in existing:
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud,
                region=settings.pinecone_region,
            ),
        )
        print(f"[Pinecone] Created index: {settings.pinecone_index_name}")
    else:
        print(f"[Pinecone] Using existing index: {settings.pinecone_index_name}")


@lru_cache(maxsize=1)
def get_vectorstore() -> PineconeVectorStore:
    """Returns a cached Pinecone vector store."""
    pc = get_pinecone_client()
    ensure_index_exists(pc)
    index = pc.Index(settings.pinecone_index_name)
    return PineconeVectorStore(
        index=index,
        embedding=get_embeddings(),
    )
