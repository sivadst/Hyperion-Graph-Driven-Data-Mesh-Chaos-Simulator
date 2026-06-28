import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hyperion.db")

settings = Settings()
