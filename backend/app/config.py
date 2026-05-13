from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password123"

    # Gemini
    GEMINI_API_KEY: str = ""

    # Embedding
    EMBEDDING_MODEL: str = "keepitreal/vietnamese-sbert"

    # App
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()