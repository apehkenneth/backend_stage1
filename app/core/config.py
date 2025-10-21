import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "String Analyzer Service"
    DATA_FILE: str = os.getenv("DATA_FILE", "data.json")


settings = Settings()