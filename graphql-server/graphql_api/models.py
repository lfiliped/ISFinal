from django.db import models

# Modelo para a tabela City
class City(models.Model):
    customer_id = models.CharField(max_length=50, primary_key=True) 
    nome = models.CharField(max_length=255)  # Nome da cidade
    estado = models.CharField(max_length=255)  # Estado da cidade
    pais = models.CharField(max_length=255)  # País da cidade
    codigo_postal = models.CharField(max_length=20, null=True, blank=True)  # Código postal (opcional)
    regiao = models.CharField(max_length=255, null=True, blank=True)  # Região (opcional)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # Latitude
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # Longitude

    class Meta:
        db_table = "cities"  # Nome da tabela no banco de dados     


# Modelo para a tabela Order
class Order(models.Model):
    order_id = models.CharField(max_length=50, primary_key=True)  # ID do pedido
    order_date = models.DateField(null=True, blank=True)  # Data do pedido (opcional)
    ship_date = models.DateField(null=True, blank=True)  # Data de envio (opcional)
    customer = models.ForeignKey(City, on_delete=models.CASCADE, db_column="customer_id")  # Relacionamento com City

    class Meta:
        db_table = "orders"  # Nome da tabela no banco de dados


# Modelo para a tabela Product
class Product(models.Model):
    product_id = models.CharField(max_length=50, primary_key=True)  # ID do produto
    product_name = models.TextField()  # Nome do produto
    category = models.CharField(max_length=50, null=True, blank=True)  # Categoria (opcional)
    sub_category = models.CharField(max_length=50, null=True, blank=True)  # Subcategoria (opcional)
    sales = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Valor de vendas (opcional)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column="order_id")  # Relacionamento com Order

    class Meta:
        db_table = "products"  # Nome da tabela no banco de dados
