class Config:
    """Base configuration."""
    SECRET_KEY = "your_secret_key"  # Replace with a strong secret key
    DEBUG = False
    TESTING = False
    DB_HOST = "skillbridgev1.c5qm0o6m67ez.us-east-2.rds.amazonaws.com"
    # skillbridgev1.c5qm0o6m67ez.us-east-2.rds.amazonaws.com
    DB_USER = "admin"
    # "admin"
    DB_PASSWORD = "skillBridge"
    # Vmzufbxg51IOJbH2ttHX
    DB_NAME = "skillBridge"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
