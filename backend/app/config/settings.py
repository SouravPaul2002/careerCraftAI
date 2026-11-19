from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App settings (defaults are used if not set in .env)
    APP_NAME: str = "CareerCraft AI"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:3000"

    # PostgreSQL database connection string
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/careercraft_ai"

    # JWT authentication settings (override SECRET_KEY in .env)
    SECRET_KEY: str = "dev-secret-key-please-override-in-env-file-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Encryption key for OAuth tokens stored in the database
    TOKEN_ENCRYPTION_KEY: str = ""

    # Google OAuth 2.0 settings (set in .env)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/integrations/google/callback"

    # GitHub OAuth App settings (set in .env)
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/integrations/github/callback"

    # Local Ollama server URL
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Groq Cloud API settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # Google Gemini API settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # LLM provider: 'auto', 'gemini', 'groq', 'ollama'
    LLM_PROVIDER: str = "auto"

    # Optional custom path for ChromaDB persistence
    CHROMA_PERSIST_DIR: str = ""

    # Tell Pydantic to read values from the .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
