import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    project_name: str = "ChatDock API"
    target_response_time: str = "1-2 seconds"
    max_context_chunks: int = 4
    chunk_size_tokens: int = 400
    chunk_overlap: int = 50
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60
    response_cache_ttl_seconds: int = Field(default=60)
    conversation_ttl_seconds: int = Field(default=60 * 60 * 2)
    conversation_max_messages: int = Field(default=16)
    auth_token_ttl_seconds: int = Field(default=60 * 60 * 12)
    secret_key: str = os.getenv("SECRET_KEY", "chatdock-dev-secret")
    environment: str = os.getenv("ENVIRONMENT", "development")

    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/chatdock")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "chatdock_chunks")

    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_max_output_tokens: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "600"))
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "openai")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/1"))
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/2"))


settings = Settings()
