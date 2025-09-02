import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "@default_user")  # Используй строку по умолчанию, если переменная не задана

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/rental_crm")

# Web Interface
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# File uploads
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
