import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "String Analyzer Service"
    DATA_FILE: str = os.getenv("DATA_FILE", "/tmp/data.json")
    PORT: int = int(os.getenv("PORT", 8000))

settings = Settings()