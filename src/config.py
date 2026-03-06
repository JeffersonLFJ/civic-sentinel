from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentinela Cívico"
    ANONYMIZATION_SALT: str = "dev_secret_salt_CHANGE_IN_PROD"
    ENV: str = "dev"  # dev | prod
    ADMIN_API_KEY: str = "dev_admin_key_CHANGE_IN_PROD"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMADB_DIR: Path = DATA_DIR / "chromadb"
    SQLITE_DB_PATH: Path = DATA_DIR / "sqlite" / "sentinela.db"
    INGEST_DIR: Path = DATA_DIR / "ingest"
    
    # LLM
    OLLAMA_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma3:27b"  # Default Factory Model
    LLM_TIMEOUT: int = 120
    
    # OCR
    OCR_MIN_CONFIDENCE: float = 70.0
    OCR_VALIDATION_THRESHOLD: float = 80.0

    # Upload & CORS
    MAX_UPLOAD_MB: int = 50
    ALLOWED_UPLOAD_MIME: str = "application/pdf,text/plain,text/html"
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]

    def allowed_upload_mime(self) -> List[str]:
        return [m.strip() for m in self.ALLOWED_UPLOAD_MIME.split(",") if m.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
