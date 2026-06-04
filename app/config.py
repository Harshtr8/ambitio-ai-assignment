from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # =========================================================================
    # GEMINI
    # =========================================================================

    GEMINI_API_KEY: str

    MODEL_NAME: str = "gemini-2.5-flash"
    MAX_OUTPUT_TOKENS: int = 2048

    # =========================================================================
    # EMBEDDINGS
    # =========================================================================

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # =========================================================================
    # OCR
    # =========================================================================

    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # =========================================================================
    # CHUNKING
    # =========================================================================

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # =========================================================================
    # RETRIEVAL
    # =========================================================================

    TOP_K_CHUNKS: int = 5

    # =========================================================================
    # PATHS
    # =========================================================================

    SAMPLE_DOCS_DIR: Path = BASE_DIR / "data" / "sample_docs"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    SAMPLE_OUTPUTS_DIR: Path = BASE_DIR / "data" / "sample_outputs"

    FAISS_INDEX_DIR: Path = BASE_DIR / "storage" / "faiss_index"

    EDIT_STORE_PATH: Path = BASE_DIR / "data" / "edit_store.json"
    LEARNED_PATTERNS_PATH: Path = BASE_DIR / "data" / "learned_patterns.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# =========================================================================
# CREATE REQUIRED DIRECTORIES ON STARTUP
# =========================================================================

for directory in [
    settings.SAMPLE_DOCS_DIR,
    settings.PROCESSED_DIR,
    settings.SAMPLE_OUTPUTS_DIR,
    settings.FAISS_INDEX_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)