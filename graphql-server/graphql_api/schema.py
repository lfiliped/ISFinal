import pika
import json
import graphene
from graphene_django.types import DjangoObjectType
from .models import Order, Product, City
import requests

# Definir o tipo de objeto para o modelo Order
class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("order_id", "customer_id", "order_date", "ship_date")

# Definir o tipo de objeto para o modelo Product
class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("product_id", "product_name", "category", "sub_category", "sales")

# Definir o tipo de objeto para o modelo City
class CityType(DjangoObjectType):
    class Meta:
        model = City
        # Inclui apenas os campos desejados, excluindo `codigo_postal`
        fields = ("customer_id", "nome", "estado", "pais", "regiao", "latitude", "longitude")

# Query para listar todas as ordens e produtos
class Query(graphene.ObjectType):
    all_orders = graphene.List(OrderType)
    all_products = graphene.List(ProductType)
    all_cities = graphene.List(CityType)

    product_by_id = graphene.Field(ProductType, product_id=graphene.String(required=True))
    products_by_category = graphene.List(ProductType, category=graphene.String(), sub_category=graphene.String())

    orders_by_date_range = graphene.List(OrderType, start_date=graphene.Date(), end_date=graphene.Date())
    orders_by_customer = graphene.List(OrderType, customer_id=graphene.String())

    city_by_customer_id = graphene.Field(CityType, customer_id=graphene.String(required=True))
    cities = graphene.List(CityType, nome=graphene.String())

    def resolve_all_orders(self, info, **kwargs):
        return Order.objects.all()

    def resolve_all_products(self, info, **kwargs):
        return Product.objects.all()

    def resolve_all_cities(self, info, **kwargs):
        return City.objects.all()

    def resolve_product_by_id(self, info, product_id):
        try:
            return Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return None

    def resolve_products_by_category(self, info, category=None, sub_category=None):
        query = Product.objects.all()
        if category:
            query = query.filter(category=category)
        if sub_category:
            query = query.filter(sub_category=sub_category)
        return query

    def resolve_orders_by_date_range(self, info, start_date=None, end_date=None):
        query = Order.objects.all()
        if start_date and end_date:
            query = query.filter(order_date__range=[start_date, end_date])
        return query

    def resolve_orders_by_customer(self, info, customer_id=None):
        if customer_id:
            return Order.objects.filter(customer_id=customer_id)
        return Order.objects.none()

    def resolve_city_by_customer_id(self, info, customer_id):
        try:
            return City.objects.get(customer_id=customer_id)
        except City.DoesNotExist:
            return None

    def resolve_cities(self, info, nome=None):
        query = City.objects.all()
        if nome:
            query = query.filter(nome__icontains=nome)
        return query

# Mutation para criar uma ordem
class CreateOrder(graphene.Mutation):
    class Arguments:
        order_id = graphene.String(required=True)
        customer_id = graphene.String(required=True)
        order_date = graphene.Date(required=True)
        ship_date = graphene.Date(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, order_id, customer_id, order_date, ship_date):
        order = Order(
            order_id=order_id,
            customer_id=customer_id,
            order_date=order_date,
            ship_date=ship_date,
        )
        order.save()
        return CreateOrder(order=order)

# Mutation para criar um produto
class CreateProduct(graphene.Mutation):
    class Arguments:
        product_id = graphene.String(required=True)
        product_name = graphene.String(required=True)
        category = graphene.String(required=True)
        sub_category = graphene.String(required=True)
        sales = graphene.Float(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, product_id, product_name, category, sub_category, sales):
        product = Product(
            product_id=product_id,
            product_name=product_name,
            category=category,
            sub_category=sub_category,
            sales=sales
        )
        product.save()
        return CreateProduct(product=product)


# Mutation para criar uma cidade
class CreateCity(graphene.Mutation):
    class Arguments:
        customer_id = graphene.String(required=True)
        nome = graphene.String(required=True)
        estado = graphene.String(required=True)
        pais = graphene.String(required=True)
        codigo_postal = graphene.String(required=True)
        regiao = graphene.String(required=True)
        latitude = graphene.Float(required=True)
        longitude = graphene.Float(required=True)

    city = graphene.Field(CityType)

    def mutate(self, info, customer_id, nome, estado, pais, codigo_postal, regiao, latitude, longitude):
        city = City(
            customer_id=customer_id,
            nome=nome,
            estado=estado,
            pais=pais,
            codigo_postal=codigo_postal,
            regiao=regiao,
            latitude=latitude,
            longitude=longitude
        )
        city.save()
        return CreateCity(city=city)
    
# Mutation para enviar mensagem para RabbitMQ
class SendMessageToRabbitMQ(graphene.Mutation):
    class Arguments:
        message = graphene.String(required=True)

    success = graphene.Boolean()
    response_message = graphene.String()

    def mutate(self, info, message):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host="rabbitmq",
                    port=5672,
                    credentials=pika.PlainCredentials("user", "password")
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="graphql_to_rest")

            # Enviar mensagem como JSON
            channel.basic_publish(
                exchange="",
                routing_key="graphql_to_rest",
                body=json.dumps({"message": message})
            )

            connection.close()
            return SendMessageToRabbitMQ(success=True, response_message="Message sent to RabbitMQ successfully.")
        except Exception as e:
            return SendMessageToRabbitMQ(success=False, response_message=str(e))

# Mutation para atualizar a latitude e longitude de uma cidade
class UpdateCity(graphene.Mutation):
    class Arguments:
        customer_id = graphene.String(required=True)
        latitude = graphene.Float(required=True)
        longitude = graphene.Float(required=True)

    city = graphene.Field(CityType)

    def mutate(self, info, customer_id, latitude, longitude):
        print(f"Received mutation to update city {customer_id} with latitude={latitude}, longitude={longitude}")
        try:
            city = City.objects.get(customer_id=customer_id)
        except City.DoesNotExist:
            print(f"City with id {customer_id} does not exist")
            raise Exception("City not found")

        # Atualiza latitude e longitude
        city.latitude = latitude
        city.longitude = longitude

        # Realiza reverse geocoding para obter nome, estado, pais, regiao
        try:
            # URL da API de reverse geocoding do Nominatim
            geocode_url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'format': 'jsonv2',
                'lat': latitude,
                'lon': longitude,
                'addressdetails': 1,
            }
            headers = {
                'User-Agent': 'YourAppName/1.0 (your.email@example.com)'  
            }
            response = requests.get(geocode_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            address = data.get('address', {})
            # Atualiza os campos com base nos dados retornados
            city.nome = address.get('city') or address.get('town') or address.get('village') or address.get('hamlet') or city.nome
            city.estado = address.get('state') or city.estado
            city.pais = address.get('country') or city.pais
            city.regiao = address.get('region') or address.get('state_district') or city.regiao

        except requests.RequestException as e:
            print(f"Reverse geocoding failed: {e}")
            raise Exception("Failed to perform reverse geocoding")

        city.save()
        print(f"Updated city {customer_id}: nome={city.nome}, estado={city.estado}, pais={city.pais}, regiao={city.regiao}, latitude={city.latitude}, longitude={city.longitude}")
        return UpdateCity(city=city)

# Atualizar a classe Mutation para incluir UpdateCity
class Mutation(graphene.ObjectType):
    create_order = CreateOrder.Field()
    create_product = CreateProduct.Field()
    send_message_to_rabbitmq = SendMessageToRabbitMQ.Field()
    create_city = CreateCity.Field()
    update_city = UpdateCity.Field()  # Adicione a mutation para atualizar cidade

# Definir o esquema
schema = graphene.Schema(query=Query, mutation=Mutation)
