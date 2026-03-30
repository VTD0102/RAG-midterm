import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Load .env relative to the 'backend' directory (not current working directory)
# __file__ is /home/.../backend/app/config.py
# .parent.parent will be /home/.../backend/
CURRENT_APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(CURRENT_APP_DIR)
ENV_FILE_PATH = os.path.join(BACKEND_ROOT, ".env")

class Settings(BaseSettings):
    # Pydantic v2 style settings configuration
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # OpenRouter API (Chat)
    openrouter_api_key: str = Field(..., validation_alias="OPENROUTER_API_KEY")
    llm_model: str = Field("google/gemini-2.0-flash-001", validation_alias="LLM_MODEL")

    # Embeddings API
    embedding_model: str = Field(
        "openai/text-embedding-3-small", validation_alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(1536, validation_alias="EMBEDDING_DIMENSION")

    # Pinecone
    pinecone_api_key: str = Field(..., validation_alias="PINECONE_API_KEY")
    pinecone_index_name: str = Field("rag-chatbot-openrouter", validation_alias="PINECONE_INDEX_NAME")
    pinecone_cloud: str = Field("aws", validation_alias="PINECONE_CLOUD")
    pinecone_region: str = Field("us-east-1", validation_alias="PINECONE_REGION")

    # Retrieval
    retriever_top_k: int = Field(5, validation_alias="RETRIEVER_TOP_K")
    bm25_weight: float = Field(0.3, validation_alias="BM25_WEIGHT")

    # App
    cors_origins: str = Field("http://localhost:3000", validation_alias="CORS_ORIGINS")
    upload_dir: str = Field("./data", validation_alias="UPLOAD_DIR")

settings = Settings()
