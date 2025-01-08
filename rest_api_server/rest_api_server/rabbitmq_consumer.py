import pika
import json
import logging
import requests
import os

# Configurações do RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PW = os.getenv("RABBITMQ_PW", "password")
QUEUE_NAME = "graphql_to_rest"

# Configurações REST
REST_API_BASE_URL = os.getenv("REST_API_BASE_URL", "http://rest-api-server:8000/api")

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def process_message(message):
    """
    Processa mensagens recebidas do RabbitMQ.
    """
    try:
        logger.info(f"Mensagem recebida: {message}")
        data = json.loads(message)
        if isinstance(data.get("message"), str):
            # Decodifique o JSON dentro do campo "message"
            data["message"] = json.loads(data["message"])
        
        # Validar a estrutura da mensagem
        if "endpoint" in data["message"] and "payload" in data["message"]:
            endpoint = data["message"]["endpoint"]
            payload = data["message"]["payload"]

            response = requests.post(f"{REST_API_BASE_URL}/{endpoint}/", json=payload)
            logger.info(f"Resposta do REST API ({endpoint}): {response.status_code} - {response.text}")
        else:
            logger.warning("Mensagem inválida ou incompleta.")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        
def consume():
    """
    Consumidor do RabbitMQ.
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PW)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    logger.info("Aguardando mensagens na fila...")
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=lambda ch, method, properties, body: process_message(body.decode("utf-8")),
        auto_ack=True
    )
    channel.start_consuming()

if __name__ == "__main__":
    consume()
