from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DB_FILE = Path(__file__).parent / "nutrition_app.db"

    @property
    def database_url(self):
        return os.getenv("DATABASE_URL", f"sqlite:///{self.DB_FILE}")

settings = Settings()
