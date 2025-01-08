import pika
import os
import logging
import time
from io import StringIO
import pandas as pd
import pg8000

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PW = os.getenv("RABBITMQ_PW", "password")
QUEUE_NAME = 'csv_chunks'

DBHOST = os.getenv('DBHOST', 'localhost')
DBUSERNAME = os.getenv('DBUSERNAME', 'myuser')
DBPASSWORD = os.getenv('DBPASSWORD', 'mypassword')
DBNAME = os.getenv('DBNAME', 'mydatabase')
DBPORT = os.getenv('DBPORT', '5435')

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()
csv_buffer = []

def validate_and_normalize_dataframe(df):
    """
    Valida e normaliza o DataFrame para garantir que contém todas as colunas necessárias.
    """
    required_columns = {
        'Row ID', 'Order ID', 'Order Date', 'Ship Date', 'Ship Mode',
        'Customer ID', 'Customer Name', 'Segment', 'Country', 'City', 'State',
        'Postal Code', 'Region', 'Retail Sales People', 'Product ID', 'Category',
        'Sub-Category', 'Product Name', 'Returned', 'Sales', 'Quantity',
        'Discount', 'Profit', 'Latitude', 'Longitude'
    }

    # Adiciona colunas ausentes com valores padrão
    for column in required_columns:
        if column not in df.columns:
            logger.warning(f"Coluna ausente no CSV: {column}. Adicionando com valores padrão.")
            df[column] = None

    # Reordena as colunas para corresponder ao conjunto esperado
    df = df[[column for column in required_columns]]
    return df

def save_to_database(df):
    """
    Salva os dados do DataFrame nas tabelas PostgreSQL.
    """
    try:
        conn = pg8000.connect(
            host=DBHOST,
            user=DBUSERNAME,
            password=DBPASSWORD,
            database=DBNAME,
            port=int(DBPORT)
        )
        cursor = conn.cursor()

        for index, row in df.iterrows():
            # **Validação: Latitude e Longitude não podem ser ambas nulas**
            latitude = row.get('Latitude')
            longitude = row.get('Longitude')
            if pd.isnull(latitude) or pd.isnull(longitude):
                logger.warning(f"Linha {index}: Latitude ou Longitude estão nulas. Linha ignorada.")
                continue

            try:
                # Inserir ou atualizar na tabela 'cities'
                cursor.execute("""
                    INSERT INTO cities (customer_id, nome, estado, pais, codigo_postal, regiao, latitude, longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO UPDATE
                    SET nome = EXCLUDED.nome,
                        estado = EXCLUDED.estado,
                        pais = EXCLUDED.pais,
                        codigo_postal = EXCLUDED.codigo_postal,
                        regiao = EXCLUDED.regiao,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude;
                """, (
                    row['Customer ID'], row['City'], row['State'], row['Country'],
                    row.get('Postal Code'), row.get('Region'),
                    latitude, longitude
                ))

                # Inserir ou atualizar na tabela 'orders'
                cursor.execute("""
                    INSERT INTO orders (order_id, order_date, ship_date, customer_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (order_id) DO UPDATE
                    SET order_date = EXCLUDED.order_date,
                        ship_date = EXCLUDED.ship_date,
                        customer_id = EXCLUDED.customer_id;
                """, (
                    row['Order ID'],
                    pd.to_datetime(row['Order Date']).date() if pd.notnull(row['Order Date']) else None,
                    pd.to_datetime(row['Ship Date']).date() if pd.notnull(row['Ship Date']) else None,
                    row['Customer ID']
                ))

                # Inserir ou atualizar na tabela 'products'
                cursor.execute("""
                    INSERT INTO products (product_id, product_name, category, sub_category, sales, order_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (product_id) DO UPDATE
                    SET product_name = EXCLUDED.product_name,
                        category = EXCLUDED.category,
                        sub_category = EXCLUDED.sub_category,
                        sales = EXCLUDED.sales,
                        order_id = EXCLUDED.order_id;
                """, (
                    row['Product ID'], row['Product Name'], row['Category'], row['Sub-Category'],
                    row.get('Sales', 0.0), row['Order ID']
                ))
                logger.info(f"Linha {index}: Dados inseridos com sucesso.")
            except Exception as e:
                logger.error(f"Linha {index}: Erro ao salvar dados: {e}")
                continue

        conn.commit()
        logger.info("Transações confirmadas no banco de dados.")

    except Exception as e:
        logger.error(f"Erro ao salvar no banco de dados: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Conexão com o banco de dados fechada.")

def process_csv_message(body):
    """
    Processa mensagens CSV recebidas do RabbitMQ.
    Acumula os chunks e processa o CSV completo ao receber o marcador de EOF.
    """
    global csv_buffer
    try:
        message = body.decode('utf-8')
        if message == "__EOF__":
            # Concatena todos os chunks
            full_csv = ''.join(csv_buffer)
            df = pd.read_csv(StringIO(full_csv))
            df = validate_and_normalize_dataframe(df)
            save_to_database(df)
            # Limpa o buffer após processamento
            csv_buffer = []
            logger.info("Arquivo CSV completo processado com sucesso.")
        else:
            # Acumula o chunk
            csv_buffer.append(message)
            logger.info(f"Chunk recebido e acumulado. Tamanho atual do buffer: {len(csv_buffer)}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem CSV: {e}")

def process_message(ch, method, properties, body):
    """
    Callback para mensagens recebidas.
    """
    try:
        if method.routing_key == QUEUE_NAME:
            process_csv_message(body)
        else:
            logger.warning(f"Fila desconhecida: {method.routing_key}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

def main():
    """
    Inicia a conexão ao RabbitMQ e processa mensagens.
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PW)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=int(RABBITMQ_PORT), credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message, auto_ack=True)

    logger.info("Aguardando mensagens na fila...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
