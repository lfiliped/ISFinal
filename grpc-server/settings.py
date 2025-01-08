import os

# gRPC Server settings
GRPC_SERVER_PORT = os.getenv("GRPC_SERVER_PORT", "50052")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))
MEDIA_PATH = os.getenv("MEDIA_PATH", "/app/media")

# Database settings
DBNAME = os.getenv("DBNAME", "mydatabase")
DBUSERNAME = os.getenv("DBUSERNAME", "myuser")
DBPASSWORD = os.getenv("DBPASSWORD", "mypassword")
DBHOST = os.getenv("DBHOST", "db")
DBPORT = os.getenv("DBPORT", "5432")

# RabbitMQ settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PW = os.getenv("RABBITMQ_PW", "password")
