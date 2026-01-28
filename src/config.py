import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "super-secret-key-change-this"

    # Database
    DATABASE_PATH = os.path.join(BASE_DIR, "attendance.db")

    # Uploads
    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload

    # Image settings
    IMAGE_SIZE = (600, 600)
    IMAGE_QUALITY = 75
