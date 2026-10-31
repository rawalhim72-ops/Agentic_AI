"""
Application Configuration and Settings Module.
Supports environment variables and .env configuration for LLM providers,
embeddings, databases, vector stores, and Langfuse tracing.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from base directory if present
load_dotenv(BASE_DIR / ".env")


class Settings:
    # Application Info
    APP_NAME: str = "Intelligent Student Support Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Base Directories
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = DATA_DIR / "logs"
    VECTOR_STORE_DIR: Path = DATA_DIR / "vector_store"
    EVALUATION_RESULTS_DIR: Path = BASE_DIR / "evaluation" / "results"
    
    # Database
    DATABASE_PATH: Path = DATA_DIR / "student_support.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH.as_posix()}"
    
    # LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    
    # Provider detection: default to groq if GROQ_API_KEY is present or LLM_API_KEY starts with gsk_
    _env_provider = os.getenv("LLM_PROVIDER", "").lower()
    if _env_provider:
        LLM_PROVIDER: str = _env_provider
    elif os.getenv("GROQ_API_KEY", "") or (os.getenv("LLM_API_KEY", "").startswith("gsk_")):
        LLM_PROVIDER: str = "groq"
    else:
        LLM_PROVIDER: str = "openai"

    # Default model based on provider
    _env_model = os.getenv("LLM_MODEL", "")
    if _env_model:
        LLM_MODEL: str = _env_model
    elif LLM_PROVIDER == "groq":
        LLM_MODEL: str = "llama-3.3-70b-versatile"
    else:
        LLM_MODEL: str = "gpt-4o-mini"

    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1" if LLM_PROVIDER == "groq" else "https://api.openai.com/v1")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    # Embedding Settings
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers").lower()
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # RAG Settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "3"))
    HANDBOOK_PDF_PATH: Path = DATA_DIR / "student_handbook.pdf"
    
    # Langfuse Tracing
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        cls.EVALUATION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    @property
    def has_groq_key(self) -> bool:
        key = self.GROQ_API_KEY or (self.LLM_API_KEY if self.LLM_PROVIDER == "groq" or self.LLM_API_KEY.startswith("gsk_") else "")
        return bool(key and not key.startswith("your_"))

    @property
    def has_openai_key(self) -> bool:
        return bool(self.LLM_API_KEY and not self.LLM_API_KEY.startswith("your_") and not self.LLM_API_KEY.startswith("gsk_"))

    @property
    def has_llm_key(self) -> bool:
        return self.has_groq_key or self.has_openai_key

    def update_llm_config(self, provider: str, api_key: str, model: str = ""):
        """Dynamically update LLM provider and credentials at runtime."""
        self.LLM_PROVIDER = provider.lower()
        if self.LLM_PROVIDER == "groq":
            self.GROQ_API_KEY = api_key.strip()
            self.LLM_API_KEY = api_key.strip()
            self.LLM_BASE_URL = "https://api.groq.com/openai/v1"
            self.LLM_MODEL = model.strip() or "llama-3.3-70b-versatile"
        else:
            self.LLM_API_KEY = api_key.strip()
            self.LLM_BASE_URL = "https://api.openai.com/v1"
            self.LLM_MODEL = model.strip() or "gpt-4o-mini"
    
    @property
    def has_langfuse(self) -> bool:
        return bool(self.LANGFUSE_PUBLIC_KEY and self.LANGFUSE_SECRET_KEY)


settings = Settings()
settings.ensure_directories()
