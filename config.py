import os

class Config:
    # Base Configurations
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL')
    
    # OAuth Configurations
    OAUTH_CLIENT_ID=os.getenv('OAUTH_CLIENT_ID')
    OAUTH_CLIENT_SECRET=os.getenv('OAUTH_CLIENT_SECRET')
    
    # RabbitMQ Configurations
    RABBITMQ_HOST=os.getenv('RABBITMQ_HOST')
    RABBITMQ_PORT=os.getenv('RABBITMQ_PORT')
    RABBITMQ_USER=os.getenv('RABBITMQ_USER')
    RABBITMQ_PASS=os.getenv('RABBITMQ_PASS')