from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Google Gemini
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    gemini_model: str = Field("gemini-2.0-flash", env="GEMINI_MODEL")
    gemini_embedding_model: str = Field(
        "models/text-embedding-004", env="GEMINI_EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(768, env="EMBEDDING_DIMENSION")

    # Pinecone
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_index_name: str = Field("rag-chatbot", env="PINECONE_INDEX_NAME")
    pinecone_cloud: str = Field("aws", env="PINECONE_CLOUD")
    pinecone_region: str = Field("us-east-1", env="PINECONE_REGION")

    # Retrieval
    retriever_top_k: int = Field(5, env="RETRIEVER_TOP_K")
    bm25_weight: float = Field(0.3, env="BM25_WEIGHT")

    # App
    cors_origins: str = Field("http://localhost:3000", env="CORS_ORIGINS")
    upload_dir: str = Field("./data", env="UPLOAD_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
