class Config:
    """Base configuration."""
    SECRET_KEY = "your_secret_key"  # Replace with a strong secret key
    DEBUG = False
    TESTING = False
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = "root"
    DB_NAME = "skillBridge"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
