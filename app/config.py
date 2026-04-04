import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY        = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
    MONGO_URI         = os.environ.get("MONGO_URI", "mongodb://localhost:27017/datalens")
    GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
    ADMIN_EMAIL       = os.environ.get("ADMIN_EMAIL", "")
    MAX_UPLOAD_MB     = int(os.environ.get("MAX_UPLOAD_MB", 50))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", 50)) * 1024 * 1024
