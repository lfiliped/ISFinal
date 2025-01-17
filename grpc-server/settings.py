import os

# gRPC Server settings
GRPC_SERVER_PORT = os.getenv("GRPC_SERVER_PORT", "50052")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))

# Antigo MEDIA_PATH agora não será usado para guardar CSV ou XML diretamente.
# Mas se ainda precisar dele para outros arquivos, pode mantê-lo.
MEDIA_PATH = os.getenv("MEDIA_PATH", "/app/media")

# Novas variáveis para os volumes:
CSV_PATH = os.getenv("CSV_PATH", "/app/csv")
XML_PATH = os.getenv("XML_PATH", "/app/xml")

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
