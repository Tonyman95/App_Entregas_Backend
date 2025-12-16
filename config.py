import os

class Config:
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-change')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_EXPIRES_SECONDS', 10800))  # 3 hours
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_EXPIRES_SECONDS', 1209600))

    # Add other configuration variables as needed
    # For example:
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///default.db')
    # DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
