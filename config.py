import os

class Config:
    # Manually set a fixed secret key
    SECRET_KEY = 'your-secret-key'  # Change this to a secure secret key
    
    # MySQL Configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Krishna@55'
    MYSQL_DB = 'college_events'
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Add charset configuration
    MYSQL_CHARSET = 'utf8mb4'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size 