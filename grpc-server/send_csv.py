import grpc
import server_services_pb2
import server_services_pb2_grpc

def send_csv():
    channel = grpc.insecure_channel('localhost:50051')
    stub = server_services_pb2_grpc.SendFileServiceStub(channel)

    # Caminho para o ficheiro CSV
    file_path = "app/csv/test.csv"
    file_name = "sample"
    file_mime = ".csv"

    with open(file_path, "rb") as file:
        file_data = file.read()

    # Enviar ficheiro via gRPC
    request = server_services_pb2.SendFileRequestBody(
        file=file_data,
        file_name=file_name,
        file_mime=file_mime
    )

    response = stub.SendFile(request)
    print(f"Success: {response.success}")

if __name__ == "__main__":
    send_csv()
