from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentinela Cívico"
    ANONYMIZATION_SALT: str = "dev_secret_salt_CHANGE_IN_PROD"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMADB_DIR: Path = DATA_DIR / "chromadb"
    SQLITE_DB_PATH: Path = DATA_DIR / "sqlite" / "sentinela.db"
    INGEST_DIR: Path = DATA_DIR / "ingest"
    
    # LLM
    OLLAMA_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma3:27b"  # Ensure model name matches what user has/needs
    LLM_TIMEOUT: int = 120
    
    # OCR
    OCR_MIN_CONFIDENCE: float = 70.0
    OCR_VALIDATION_THRESHOLD: float = 80.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
