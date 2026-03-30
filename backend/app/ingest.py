"""
Document ingestion pipeline.
Supports PDF, TXT, DOCX, and Markdown files.
Chunks documents and upserts embeddings into Pinecone.
"""
import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)

from app.config import settings
from app.vectorstore import get_vectorstore

# ── Chunking config ────────────────────────────────────────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_document(file_path: str) -> List[Document]:
    """Load a file based on its extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in (".txt", ".md"):
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext in (".docx", ".doc"):
        loader = UnstructuredWordDocumentLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader.load()


async def ingest_file(file_path: str, filename: str) -> int:
    """
    Load, chunk, and index a file into Pinecone.
    Returns the number of chunks indexed.
    """
    docs = load_document(file_path)

    # Attach source metadata
    for doc in docs:
        doc.metadata["source"] = filename

    # Split into chunks
    chunks = splitter.split_documents(docs)

    if not chunks:
        return 0

    # Upsert into Pinecone (batched automatically by langchain-pinecone)
    vectorstore = get_vectorstore()
    await vectorstore.aadd_documents(chunks)

    return len(chunks)
