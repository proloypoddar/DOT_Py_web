import os
from datetime import timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # MongoDB settings
    MONGO_URI = "mongodb+srv://iamproloy9:lXYO9qd6tLccYrJ8@cluster0.ylvnn2h.mongodb.net/myDatabase?retryWrites=true&w=majority&appName=Cluster0"
    MONGO_DB_NAME = "myDatabase"
    
    @staticmethod
    def get_mongo_client():
        """Get MongoDB client instance with connection handling"""
        try:
            client = MongoClient(Config.MONGO_URI)
            # Test the connection
            client.admin.command('ping')
            return client
        except ConnectionFailure as e:
            raise Exception(f"Failed to connect to MongoDB: {e}")
    
    @staticmethod
    def get_database():
        """Get database instance"""
        client = Config.get_mongo_client()
        return client['myDatabase']
    
    # Email settings (for contact form)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security settings
    SESSION_COOKIE_SECURE = False  # Allow HTTP sessions for development
    REMEMBER_COOKIE_SECURE = False  # Allow HTTP remember cookies for development
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # Google Sheets Integration
    GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw4un8HujGfTXb08iILT4V_V2Ot-bGYYh6tcLD5khwMD-ZZsGxG8SSwmsZaMn1sdiimDg/exec"

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # In production, use environment variables for sensitive data
    SECRET_KEY = os.environ.get('SECRET_KEY')

class TestingConfig(Config):
    TESTING = True
    MONGO_URI = Config.MONGO_URI  # Use the same database for testing

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 