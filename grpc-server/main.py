import os
import server_services_pb2_grpc
import server_services_pb2
import grpc
import logging
import pg8000
import pika
import pandas as pd
from lxml import etree
from geopy.geocoders import Nominatim
import time
from concurrent import futures
import csv

from settings import (
    GRPC_SERVER_PORT,
    MAX_WORKERS,
    MEDIA_PATH,
    DBNAME,
    DBUSERNAME,
    DBPASSWORD,
    DBHOST,
    DBPORT,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PW
)

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("FileService")

def geocode_csv(input_csv_path, output_csv_path):
    geolocator = Nominatim(user_agent="grpc_geocoder")
    updated_rows = []

    with open(input_csv_path, mode='r', newline='', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        if "Latitude" not in fieldnames or "Longitude" not in fieldnames:
            new_fieldnames = fieldnames + ["Latitude", "Longitude"]
        else:
            new_fieldnames = fieldnames

        for row in reader:
            if "Latitude" in row and row["Latitude"] and "Longitude" in row and row["Longitude"]:
                updated_rows.append(row)
                continue

            address = f"{row.get('City', '')}, {row.get('State', '')}, {row.get('Postal Code', '')}, {row.get('Country', '')}"
            latitude, longitude = "", ""
            try:
                location = geolocator.geocode(address)
                if location:
                    latitude = location.latitude
                    longitude = location.longitude
            except Exception as e:
                logger.error(f"Erro ao geocodificar '{address}': {e}")

            row["Latitude"] = latitude
            row["Longitude"] = longitude
            updated_rows.append(row)
            time.sleep(1)

    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

def SendRabbitMQMessage(message):
    """
    Função auxiliar para enviar mensagens para o RabbitMQ.
    """
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PW)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=int(RABBITMQ_PORT),
                credentials=credentials
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue="csv_chunks", durable=True)

        channel.basic_publish(exchange='', routing_key="csv_chunks", body=message)
        logger.info(f"Mensagem enviada para RabbitMQ: {message}")

        connection.close()
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem para RabbitMQ: {e}", exc_info=True)

class SendFileService(server_services_pb2_grpc.SendFileServiceServicer):
    def __init__(self, *args, **kwargs):
        pass

    def SendFile(self, request, context):
        os.makedirs(MEDIA_PATH, exist_ok=True)
        file_path = os.path.join(MEDIA_PATH, request.file_name + request.file_mime)
        ficheiro_em_bytes = request.file
        with open(file_path, 'wb') as f:
            f.write(ficheiro_em_bytes)

        logger.info(f"File saved at: {file_path}")

        try:
            # Conectar ao banco de dados
            conn = pg8000.connect(
                user=DBUSERNAME, password=DBPASSWORD, host=DBHOST, port=int(DBPORT), database=DBNAME
            )
            cursor = conn.cursor()

            # **Criar tabela de cidades (cities)**
            create_table_cities = """
            CREATE TABLE IF NOT EXISTS cities (
                customer_id VARCHAR(50) PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                estado VARCHAR(255) NOT NULL,
                pais VARCHAR(255) NOT NULL,
                codigo_postal VARCHAR(20),
                regiao VARCHAR(255),
                latitude DECIMAL(9,6),
                longitude DECIMAL(9,6)
            );
            """
            cursor.execute(create_table_cities)
            
            # Criar tabela de pedidos (orders)
            create_table_orders = """
            CREATE TABLE IF NOT EXISTS orders (
                order_id VARCHAR(50) PRIMARY KEY,
                order_date DATE,
                ship_date DATE,
                customer_id VARCHAR(50),
                FOREIGN KEY (customer_id) REFERENCES cities(customer_id)
            );
            """
            cursor.execute(create_table_orders)

            # Criar tabela de produtos (products)
            create_table_products = """
            CREATE TABLE IF NOT EXISTS products (
                product_id VARCHAR(50) PRIMARY KEY,
                product_name TEXT,
                category VARCHAR(50),
                sub_category VARCHAR(50),
                sales NUMERIC,
                order_id VARCHAR(50),
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            );
            """
            cursor.execute(create_table_products)

            # Confirmar as alterações no banco de dados
            conn.commit()

            logger.info("Tables created successfully.")
            return server_services_pb2.SendFileResponseBody(success=True)

        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            context.set_details(f"Failed: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.SendFileResponseBody(success=False)

        finally:
            if conn:
                cursor.close()
                conn.close()


    def SendFileChunks(self, request_iterator, context):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PW)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=int(RABBITMQ_PORT), credentials=credentials
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="csv_chunks", durable=True)

            for chunk in request_iterator:
                logger.info(f"Enviando chunk para RabbitMQ: {chunk.data[:50]}...")  # Log apenas os primeiros 50 caracteres
                channel.basic_publish(exchange="", routing_key="csv_chunks", body=chunk.data)

            logger.info("Enviando marcador de EOF")
            channel.basic_publish(exchange="", routing_key="csv_chunks", body="__EOF__")
            connection.close()
            return server_services_pb2.SendFileChunksResponse(message="Chunks sent to RabbitMQ successfully!")
        except Exception as e:
            logger.error(f"Erro ao enviar chunks: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.SendFileChunksResponse(message="Failed to send chunks to RabbitMQ.")


    def ConvertCSVToXML(self, request, context):
        """
        Converte um arquivo CSV para XML e envia uma mensagem para o RabbitMQ.
        """
        try:
            # Capturando o nome do arquivo
            file_name = request.file_name.strip()
            logger.info(f"Nome do arquivo recebido: '{file_name}'")

            # Validando o nome do arquivo
            if not file_name or not file_name.endswith('.csv'):
                context.set_details("O nome do arquivo CSV é inválido ou não foi fornecido.")
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                SendRabbitMQMessage(f"Erro: Nome do arquivo inválido: '{file_name}'")
                return server_services_pb2.ConvertCSVToXMLResponse(success=False, message="Nome do arquivo inválido.")

            # Construindo o caminho completo do arquivo
            csv_path = os.path.join(MEDIA_PATH, file_name)
            enriched_csv_path = os.path.join(MEDIA_PATH, f"enriched_{file_name}")
            logger.info(f"Caminho completo do arquivo: {csv_path}")

            # Verificando a existência do arquivo
            if not os.path.exists(csv_path):
                context.set_details("O arquivo CSV especificado não foi encontrado.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                SendRabbitMQMessage(f"Erro: Arquivo não encontrado: '{csv_path}'")
                return server_services_pb2.ConvertCSVToXMLResponse(success=False, message="Arquivo não encontrado.")

            # Enriquecer o CSV com latitude e longitude
            geocode_csv(csv_path, enriched_csv_path)
            logger.info(f"CSV enriquecido salvo em: {enriched_csv_path}")

            # Lendo o conteúdo do CSV enriquecido
            with open(enriched_csv_path, 'r', encoding='utf-8') as file:
                csv_content = file.read()

            logger.info(f"Conteúdo do CSV lido: {csv_content[:100]}...")

            # Convertendo CSV para XML
            df = pd.read_csv(enriched_csv_path)
            root = etree.Element("Root")

            for _, row in df.iterrows():
                record = etree.SubElement(root, "Record")
                for col_name, value in row.items():
                    sanitized_col_name = col_name.replace(" ", "_").replace("-", "_")
                    child = etree.SubElement(record, sanitized_col_name)
                    child.text = str(value)

            # Salvando o arquivo XML
            output_path = os.path.join(MEDIA_PATH, file_name.replace('.csv', '.xml'))
            tree = etree.ElementTree(root)
            tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")

            logger.info(f"XML criado com sucesso em: {output_path}")

            # Enviando mensagem de sucesso para o RabbitMQ
            success_message = f"Sucesso: Conversão de '{file_name}' para XML concluída. XML salvo em: '{output_path}'"
            SendRabbitMQMessage(success_message)

            return server_services_pb2.ConvertCSVToXMLResponse(success=True, message="Conversão bem-sucedida.")
        except Exception as e:
            logger.error(f"Erro durante a conversão CSV para XML: {e}", exc_info=True)
            error_message = f"Erro: {str(e)}"
            SendRabbitMQMessage(error_message)
            context.set_details(f"Erro: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.ConvertCSVToXMLResponse(success=False, message=str(e))


    def ValidateXML(self, request, context):
        """
        Valida um arquivo XML contra um esquema XSD.
        """
        try:
            # Captura os nomes dos arquivos
            xml_file_name = request.xml_file_name.strip()
            xsd_file_name = request.xsd_file_name.strip()
            logger.info(f"Nome do arquivo XML recebido: '{xml_file_name}'")
            logger.info(f"Nome do arquivo XSD recebido: '{xsd_file_name}'")

            # Construindo os caminhos completos dos arquivos
            xml_path = os.path.join(MEDIA_PATH, xml_file_name)
            xsd_path = os.path.join(MEDIA_PATH, xsd_file_name)
            logger.info(f"Caminho do arquivo XML: {xml_path}")
            logger.info(f"Caminho do arquivo XSD: {xsd_path}")

            # Validando a existência dos arquivos
            if not os.path.exists(xml_path):
                context.set_details("O arquivo XML especificado não foi encontrado.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return server_services_pb2.ValidateXMLResponse(success=False, message="Arquivo XML não encontrado.")

            if not os.path.exists(xsd_path):
                context.set_details("O arquivo XSD especificado não foi encontrado.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return server_services_pb2.ValidateXMLResponse(success=False, message="Arquivo XSD não encontrado.")

            # Validando o XML usando o XSD
            with open(xsd_path, 'rb') as xsd_file:
                schema_root = etree.XML(xsd_file.read())
                schema = etree.XMLSchema(schema_root)
                parser = etree.XMLParser(schema=schema)
                with open(xml_path, 'rb') as xml_file:
                    etree.fromstring(xml_file.read(), parser)

            logger.info("Validação XML concluída com sucesso.")
            return server_services_pb2.ValidateXMLResponse(success=True, message="Validação bem-sucedida.")
        except etree.XMLSchemaError as e:
            logger.error(f"Erro de esquema XSD: {e}", exc_info=True)
            context.set_details(f"Erro de validação: {str(e)}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return server_services_pb2.ValidateXMLResponse(success=False, message=f"Erro de validação: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao validar XML: {e}", exc_info=True)
            context.set_details(f"Erro: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.ValidateXMLResponse(success=False, message=str(e))   

    def TextSearch(self, request, context):
        """
        Realiza uma pesquisa de texto em um arquivo XML e envia resultados para o RabbitMQ.
        """
        try:
            # Captura o nome do arquivo XML e o termo de pesquisa
            xml_file_name = request.xml_file_name.strip()
            search_term = request.search_term.strip()
            logger.info(f"Arquivo XML: '{xml_file_name}', Termo de pesquisa: '{search_term}'")

            # Construindo o caminho completo do arquivo XML
            xml_path = os.path.join(MEDIA_PATH, xml_file_name)
            if not os.path.exists(xml_path):
                context.set_details("Arquivo XML não encontrado.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                SendRabbitMQMessage(f"Erro: Arquivo XML não encontrado: '{xml_path}'")
                return server_services_pb2.TextSearchResponse(results=[])

            # Parseando o XML e realizando a pesquisa
            tree = etree.parse(xml_path)
            # Procurar os nós que contêm o termo de pesquisa
            elements = tree.xpath(f"//*[contains(text(), '{search_term}')]")
            
            # Obter o nó pai de cada elemento encontrado e converter para string
            results = []
            for elem in elements:
                parent = elem.getparent()  # Obter o nó pai
                if parent is not None:
                    results.append(etree.tostring(parent, pretty_print=True).decode("utf-8"))

            logger.info(f"Resultados encontrados: {len(results)}")

            # Enviando mensagem de sucesso para o RabbitMQ
            success_message = f"Sucesso: Pesquisa de termo '{search_term}' no arquivo '{xml_file_name}' concluída. {len(results)} resultados encontrados."
            SendRabbitMQMessage(success_message)

            return server_services_pb2.TextSearchResponse(results=results)
        except Exception as e:
            logger.error(f"Erro na pesquisa por texto: {e}", exc_info=True)
            error_message = f"Erro: {str(e)}"
            SendRabbitMQMessage(error_message)
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.TextSearchResponse(results=[])

    def ListXMLFiles(self, request, context):
        """
        Lista todos os arquivos XML disponíveis no diretório de mídia.
        """
        try:
            media_path = MEDIA_PATH  # Utilizar a variável definida nas configurações
            if not os.path.exists(media_path):
                context.set_details("Diretório de mídia não encontrado.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return server_services_pb2.ListXMLFilesResponse()

            xml_files = [f for f in os.listdir(media_path) if f.endswith('.xml')]
            return server_services_pb2.ListXMLFilesResponse(file_names=xml_files)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.ListXMLFilesResponse()

    def ListCSVFiles(self, request, context):
        """
        Lista todos os arquivos CSV disponíveis no diretório de mídia.
        """
        try:
            media_path = MEDIA_PATH  # Utilizar a variável definida nas configurações
            if not os.path.exists(media_path):
                context.set_details("Diretório de mídia não encontrado.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return server_services_pb2.ListCSVFilesResponse()

            csv_files = [f for f in os.listdir(media_path) if f.endswith('.csv')]
            return server_services_pb2.ListCSVFilesResponse(file_names=csv_files)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.ListCSVFilesResponse()
        
    def SortXML(self, request, context):
        """
        Ordena um arquivo XML com base em um campo específico e envia o resultado para o RabbitMQ.
        """
        try:
            # Captura o nome do arquivo e os parâmetros de ordenação
            xml_file_name = request.xml_file_name.strip()
            sort_by = request.sort_by.strip()
            order = request.order.strip().lower()
            logger.info(f"Ordenando XML: '{xml_file_name}' por '{sort_by}' em ordem '{order}'")

            # Caminho do arquivo XML
            xml_path = os.path.join(MEDIA_PATH, xml_file_name)

            # Verificar se o arquivo existe
            if not os.path.exists(xml_path):
                error_message = f"Erro: Arquivo XML não encontrado: '{xml_path}'"
                context.set_details("Arquivo XML não encontrado.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                SendRabbitMQMessage(error_message)
                return server_services_pb2.SortXMLResponse(success=False, message="Arquivo XML não encontrado.")

            # Parseando o XML
            tree = etree.parse(xml_path)
            root = tree.getroot()

            # Verificar se o campo de ordenação existe no XML
            if not any(child.find(sort_by) is not None for child in root):
                error_message = f"Erro: Campo '{sort_by}' não encontrado no XML."
                context.set_details(f"O campo '{sort_by}' não foi encontrado no XML.")
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                SendRabbitMQMessage(error_message)
                return server_services_pb2.SortXMLResponse(success=False, message=f"Campo '{sort_by}' não encontrado.")

            # Determinar a ordem de classificação
            reverse = order == "desc"

            # Função de chave para a ordenação, tratando valores nulos ou inexistentes
            def sort_key(elem):
                field = elem.find(sort_by)
                return field.text if field is not None and field.text is not None else ""

            # Ordenar os elementos
            root[:] = sorted(
                root,
                key=sort_key,
                reverse=reverse,
            )

            # Salvar o XML ordenado
            sorted_xml_path = os.path.join(MEDIA_PATH, f"sorted_{xml_file_name}")
            tree.write(sorted_xml_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")

            logger.info(f"XML ordenado salvo em: '{sorted_xml_path}'")

            # Ler o conteúdo do XML ordenado
            with open(sorted_xml_path, 'r', encoding='utf-8') as f:
                sorted_xml_content = f.read()

            # Enviar mensagem de sucesso para o RabbitMQ
            success_message = (
                f"Sucesso: Ordenação do arquivo '{xml_file_name}' concluída. "
                f"Arquivo ordenado salvo em: '{sorted_xml_path}'. "
                f"Ordenado por: '{sort_by}' em ordem: '{order}'."
            )
            SendRabbitMQMessage(success_message)

            return server_services_pb2.SortXMLResponse(
                success=True,
                message="Ordenação bem-sucedida.",
                sorted_xml=sorted_xml_content
            )

        except Exception as e:
            logger.error(f"Erro ao ordenar XML: {e}", exc_info=True)
            error_message = f"Erro: {str(e)}"
            SendRabbitMQMessage(error_message)
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return server_services_pb2.SortXMLResponse(success=False, message=str(e))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKERS))
    server_services_pb2_grpc.add_SendFileServiceServicer_to_server(SendFileService(), server)
    server.add_insecure_port(f"[::]:{GRPC_SERVER_PORT}")
    server.start()
    logger.info(f"gRPC server started on port {GRPC_SERVER_PORT}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
