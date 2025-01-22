from venv import logger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers.file_serializer import FileUploadSerializer
import grpc
import api.grpc.server_services_pb2 as server_services_pb2
import api.grpc.server_services_pb2_grpc as server_services_pb2_grpc
import os
from lxml import etree
from rest_api_server.settings import GRPC_PORT, GRPC_HOST, RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PW, CSV_PATH, XML_PATH
import lxml.etree as ET
import pika

# Configurações do RabbitMQ a partir das variáveis de ambiente
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PW = os.getenv("RABBITMQ_PW", "password")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PW)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=int(RABBITMQ_PORT),
        credentials=credentials
    )
)

class FileUploadView(APIView):
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error("Serializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtém os arquivos (podem ser ambos ou somente um deles)
        csv_file = serializer.validated_data.get('file')
        schema_file = serializer.validated_data.get('schema_file')
        
        # Se nenhum dos arquivos foi enviado, retorna erro
        if not csv_file and not schema_file:
            return Response({"error": "Nenhum arquivo foi enviado."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        response_data = {}
        
        # Se foi enviado o CSV, processa-o
        if csv_file:
            csv_file_name, csv_file_extension = os.path.splitext(csv_file.name)
            csv_file_content = csv_file.read()
            
            # Envia os chunks do CSV para o RabbitMQ
            try:
                credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PW)
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=RABBITMQ_HOST,
                        port=int(RABBITMQ_PORT),
                        credentials=credentials,
                    )
                )
                channel = connection.channel()
                channel.queue_declare(queue="REQUESTS", durable=True)
                
                CHUNK_SIZE = 1024
                for i in range(0, len(csv_file_content), CHUNK_SIZE):
                    chunk = csv_file_content[i:i + CHUNK_SIZE]
                    channel.basic_publish(exchange="", routing_key="REQUESTS", body=chunk)
                channel.basic_publish(exchange="", routing_key="REQUESTS", body="__EOF__")
            except Exception as e:
                logger.error("Erro ao enviar chunks para RabbitMQ: %s", e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                connection.close()
            
            # Envia o CSV completo via gRPC
            try:
                grpc_channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
                stub = server_services_pb2_grpc.SendFileServiceStub(grpc_channel)
                grpc_request = server_services_pb2.SendFileRequestBody(
                    file_name=csv_file_name,
                    file_mime=csv_file_extension,
                    file=csv_file_content,
                )
                grpc_response = stub.SendFile(grpc_request)
                response_data["file_name"] = csv_file_name
                response_data["file_extension"] = csv_file_extension
            except grpc.RpcError as e:
                logger.error("Erro gRPC: %s", e.details())
                return Response({"error": f"gRPC call failed: {e.details()}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Se foi enviado o schema (XML), processa-o
        if schema_file:
            schema_file_name, _ = os.path.splitext(schema_file.name)
            schema_file_content = schema_file.read()
            try:
                # Usa o diretório XML definido na variável XML_PATH
                os.makedirs(XML_PATH, exist_ok=True)
                schema_path = os.path.join(XML_PATH, schema_file_name)
                with open(schema_path, "wb") as f:
                    f.write(schema_file_content)
                response_data["schema_file"] = schema_file_name
            except Exception as e:
                logger.error("Erro ao salvar o arquivo de esquema: %s", e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(response_data, status=status.HTTP_201_CREATED)

class ListXMLFilesView(APIView):
    def get(self, request):
        try:
            # Conectar ao servidor gRPC para listagem dos arquivos XML
            channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
            stub = server_services_pb2_grpc.SendFileServiceStub(channel)
            grpc_request = server_services_pb2.ListXMLFilesRequest()
            grpc_response = stub.ListXMLFiles(grpc_request)
            
            # Converter o resultado para uma lista Python
            file_names = list(grpc_response.file_names)
            
            return Response({"file_names": file_names}, status=status.HTTP_200_OK)
        except grpc.RpcError as e:
            return Response({"error": f"gRPC call failed: {e.details()}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ListCSVFilesView(APIView):
    def get(self, request):
        try:
            channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
            stub = server_services_pb2_grpc.SendFileServiceStub(channel)
            grpc_request = server_services_pb2.ListCSVFilesRequest()
            grpc_response = stub.ListCSVFiles(grpc_request)
            
            
            file_names = list(grpc_response.file_names)
            
            return Response({"file_names": file_names}, status=status.HTTP_200_OK)
        except grpc.RpcError as e:
            return Response(
                {"error": f"gRPC call failed: {e.details()}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class FileUploadChunksView(APIView):
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            if not file:
                return Response({"error": "No file uploaded"}, status=400)

            file_name, file_extension = os.path.splitext(file.name)
            file_content = file.read()

            # Enviar os chunks do arquivo CSV para o RabbitMQ
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PW)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=int(RABBITMQ_PORT),
                    credentials=credentials,
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="csv_chunks", durable=True)

            try:
                CHUNK_SIZE = 1024
                for i in range(0, len(file_content), CHUNK_SIZE):
                    chunk = file_content[i:i + CHUNK_SIZE]
                    logger.info(f"Enviando chunk [{i}:{i + CHUNK_SIZE}]")
                    channel.basic_publish(exchange="", routing_key="csv_chunks", body=chunk)

                logger.info("Enviando marcador de EOF")
                channel.basic_publish(exchange="", routing_key="csv_chunks", body="__EOF__")
            except Exception as e:
                logger.error(f"Erro ao enviar chunks para RabbitMQ: {e}")
                return Response({"error": str(e)}, status=500)
            finally:
                connection.close()

            # Envia o arquivo completo via gRPC
            try:
                channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
                stub = server_services_pb2_grpc.SendFileServiceStub(channel)
                grpc_request = server_services_pb2.SendFileRequestBody(
                    file_name=file_name,
                    file_mime=file_extension,
                    file=file_content,
                )
                grpc_response = stub.SendFile(grpc_request)
                return Response(
                    {"file_name": file_name, "file_extension": file_extension},
                    status=status.HTTP_201_CREATED,
                )
            except grpc.RpcError as e:
                logger.error(f"Erro gRPC: {e.details()}")
                return Response({"error": f"gRPC call failed: {e.details()}"}, status=500)

        return Response(serializer.errors, status=400)
    
class XMLFilterByCity(APIView):
    def post(self, request):
        try:
            file_name = request.data.get("file_name")
            xpath_query = request.data.get("xpath_query")

            if not file_name or not xpath_query:
                return Response({"error": "File name and XPath query are required."}, status=status.HTTP_400_BAD_REQUEST)

            # O arquivo XML agora está no diretório definido por XML_PATH
            file_path = os.path.join(XML_PATH, file_name)
            if not os.path.exists(file_path):
                return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

            # Carregar e executar a query XPath
            tree = ET.parse(file_path)
            root = tree.getroot()
            result = root.xpath(xpath_query)

            # Converter os resultados para string
            output = [ET.tostring(element).decode("utf-8") for element in result]
            return Response({"result": output}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConvertCSVtoXMLView(APIView):
    """
    Endpoint para converter CSV em XML usando o método ConvertCSVToXML do servidor gRPC.
    Se o arquivo for enviado como form-data, é utilizado seu nome; se não, espera um JSON com 'file_name'.
    O servidor gRPC usará esse nome para localizar o arquivo.
    """
    def post(self, request):
        # Tenta extrair o arquivo enviado 
        csv_file = request.FILES.get('file')
        if csv_file:
            file_name = csv_file.name
        else:
            # Se não houver arquivo em request.FILES, tenta extrair do JSON
            file_name = request.data.get('file_name')       
        if not file_name:
            return Response({"error": "Nenhum arquivo CSV foi fornecido."},
                            status=status.HTTP_400_BAD_REQUEST)        
        try:
            # Conectar ao servidor gRPC
            channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
            stub = server_services_pb2_grpc.SendFileServiceStub(channel)
            # Cria a requisição com o nome do arquivo recebido
            grpc_request = server_services_pb2.ConvertCSVToXMLRequest(file_name=file_name)
            grpc_response = stub.ConvertCSVToXML(grpc_request)            
            return Response({
                "success": grpc_response.success,
                "message": grpc_response.message
            }, status=status.HTTP_200_OK)
        except grpc.RpcError as e:
            return Response({"error": f"gRPC call failed: {e.details()}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class ValidateXMLView(APIView):
    def post(self, request):
        # Receber os arquivos enviados no formulário
        xml_file = request.FILES.get('file')
        xsd_file = request.FILES.get('file_xsd')

        if not xml_file or not xsd_file:
            return Response({"error": "Both XML file and XSD file are required."}, status=400)

        # Salvar os arquivos no diretório XML
        os.makedirs(XML_PATH, exist_ok=True)

        xml_file_name = xml_file.name
        xsd_file_name = xsd_file.name

        xml_path = os.path.join(XML_PATH, xml_file_name)
        xsd_path = os.path.join(XML_PATH, xsd_file_name)

        with open(xml_path, 'wb') as f:
            f.write(xml_file.read())

        with open(xsd_path, 'wb') as f:
            f.write(xsd_file.read())

        # Conectar ao servidor gRPC
        channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
        stub = server_services_pb2_grpc.SendFileServiceStub(channel)

        # Chamar o método ValidateXML do servidor gRPC
        try:
            grpc_request = server_services_pb2.ValidateXMLRequest(
                xml_file_name=xml_file_name,
                xsd_file_name=xsd_file_name
            )
            grpc_response = stub.ValidateXML(grpc_request)

            return Response({
                "success": grpc_response.success,
                "message": grpc_response.message
            }, status=200 if grpc_response.success else 400)
        except grpc.RpcError as e:
            return Response({"error": f"gRPC call failed: {e.details()}"},
                            status=500)
        
        
class XMLTextSearchView(APIView):
    def post(self, request):
        try:
            xml_file_name = request.data.get("xml_file_name")
            search_term = request.data.get("search_term")
            
            if not xml_file_name or not search_term:
                logger.warning("Nome do arquivo XML ou termo de pesquisa não fornecido.")
                return Response(
                    {"message": "Nome do arquivo XML e termo de pesquisa são obrigatórios."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file_path = os.path.join(XML_PATH, xml_file_name)
            if not os.path.exists(file_path):
                logger.error(f"Arquivo XML não encontrado: {file_path}")
                return Response(
                    {"message": "Arquivo XML não encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Parseando o XML
            tree = etree.parse(file_path)
            # Realizando a busca com XPath
            elements = tree.xpath(f"//*[contains(text(), '{search_term}')]")
            
            # Coletando os elementos pais dos nós encontrados
            results = [
                etree.tostring(elem.getparent(), pretty_print=True).decode("utf-8")
                for elem in elements if elem.getparent() is not None
            ]
            
            logger.info(f"Pesquisa realizada com sucesso. Termo: '{search_term}'. Resultados encontrados: {len(results)}")
            return Response({"results": results}, status=status.HTTP_200_OK)
        
        except etree.XMLSyntaxError as e:
            logger.exception(f"Erro de sintaxe XML: {str(e)}")
            return Response(
                {"message": "Erro de sintaxe no arquivo XML."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Erro inesperado no XMLTextSearchView: {str(e)}")
            return Response(
                {"message": "Erro interno do servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
class SortXMLView(APIView):
    """
    Endpoint para ordenar elementos em um arquivo XML.
    """
    def post(self, request):
        # Extrair os dados do corpo da requisição
        xml_file_name = request.data.get("xml_file_name")
        sort_by = request.data.get("sort_by")
        order = request.data.get("order", "asc").lower()  

        if not xml_file_name or not sort_by:
            return Response(
                {"error": "XML file name and sort_by field are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar a ordem
        if order not in ["asc", "desc"]:
            return Response(
                {"error": "Order must be 'asc' or 'desc'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Conectar ao servidor gRPC
        channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
        stub = server_services_pb2_grpc.SendFileServiceStub(channel)

        # Chamar o método SortXML
        try:
            grpc_request = server_services_pb2.SortXMLRequest(
                xml_file_name=xml_file_name,
                sort_by=sort_by,
                order=order,
            )
            grpc_response = stub.SortXML(grpc_request)

            if grpc_response.success:
                return Response(
                    {
                        "message": grpc_response.message,
                        "sorted_xml": grpc_response.sorted_xml,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": grpc_response.message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except grpc.RpcError as e:
            return Response(
                {"error": f"gRPC call failed: {e.details()}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
