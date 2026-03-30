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

import asyncio
from app.config import settings
from app.vectorstore import get_vectorstore

# ── Chunking config ────────────────────────────────────────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
# Gemini Free Tier limit is 100 RPM. We'll batch to be safe.
BATCH_SIZE = 40 
SLEEP_TIME = 10  # Seconds between batches

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

    vectorstore = get_vectorstore()
    
    # Process in batches to avoid rate limits
    total_chunks = len(chunks)
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        print(f"Ingesting batch {i//BATCH_SIZE + 1}/{(total_chunks-1)//BATCH_SIZE + 1} ({len(batch)} chunks)...")
        await vectorstore.aadd_documents(batch)
        
        # Don't sleep after the last batch
        if i + BATCH_SIZE < total_chunks:
            await asyncio.sleep(SLEEP_TIME)

    return total_chunks
