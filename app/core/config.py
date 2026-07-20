from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = ''
    JWT_EXPIRE_MINUTES: int = 60 
    JWT_ALGORITHM: str = ''

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()