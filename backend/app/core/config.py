from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///./supportflow.db"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # External APIs
    TAVILY_API_KEY: Optional[str] = None

    # App Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Agent Configuration
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_AGENT_ITERATIONS: int = 10

    # Vector Store
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
