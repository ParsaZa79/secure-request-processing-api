import os
from datetime import timedelta


class Config:
    # Base Configurations
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL')
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY')
    API_URL=os.getenv('API_URL')
    
    # OAuth Configurations
    GOOGLE_OAUTH_CLIENT_ID=os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    GOOGLE_OAUTH_REDIRECT_URI=os.getenv('GOOGLE_OAUTH_REDIRECT_URI')
    
    GITHUB_OAUTH_CLIENT_ID=os.getenv('GITHUB_OAUTH_CLIENT_ID')
    GITHUB_OAUTH_CLIENT_SECRET=os.getenv('GITHUB_OAUTH_CLIENT_SECRET')
    GITHUB_OAUTH_REDIRECT_URI=os.getenv('GITHUB_OAUTH_REDIRECT_URI')
    
    # SESSION-Related Configurations
    SESSION_TYPE='filesystem'
    SESSION_PERMANENT=True
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=5)
    
    # RabbitMQ Configurations
    RABBITMQ_HOST=os.getenv('RABBITMQ_HOST')
    RABBITMQ_PORT=os.getenv('RABBITMQ_PORT')
    RABBITMQ_USER=os.getenv('RABBITMQ_USER')
    RABBITMQ_PASS=os.getenv('RABBITMQ_PASS')