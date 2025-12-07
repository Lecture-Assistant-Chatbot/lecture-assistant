from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)  # Cloud Run will pass PORT; we’ll override in main
    log_level: str = Field(default="info")
    cors_allow_all: bool = Field(default=True)

    # Vertex AI
    google_cloud_project: str = Field(..., alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(..., alias="GOOGLE_CLOUD_LOCATION")
    google_genai_use_vertexai: bool = Field(default=True, alias="GOOGLE_GENAI_USE_VERTEXAI")

    # Matching Engine (Vector Search)
    vertex_ai_index_endpoint: str = Field(..., alias="VERTEX_AI_INDEX_ENDPOINT")
    vertex_ai_deployed_index: str = Field(..., alias="VERTEX_AI_DEPLOYED_INDEX")

    # Gemini API
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash-preview-09-2025", alias="GEMINI_MODEL")

    # Timeouts
    http_timeout_seconds: int = Field(default=60)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()  # evaluate once at import
