import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MAX_CONTENT_LENGTH_MB = int(os.getenv("MAX_CONTENT_LENGTH_MB", "2048"))  # 2GB default
