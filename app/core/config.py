from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = ''
    JWT_EXPIRE_MINUTES: int = 60 
    JWT_ALGORITHM: str = ''

    AGENT_SERVICE_URL: str = "http://agent_service:8001"
    XGBOOST_SERVICE_URL: str = "http://xgboost_service:8002"
    INTERNAL_SERVICE_TOKEN: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()