from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

class GetAllOrders(APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM orders")
            result = cursor.fetchall()
        
        orders = [
            {
                "id": order[0],
                "order_id": order[1],
                "order_date": order[2],
                "ship_date": order[3],
                "customer_id": order[4]
            }
            for order in result
        ]
        
        return Response({"orders": orders}, status=status.HTTP_200_OK)

class GetAllProducts(APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM products")
            result = cursor.fetchall()
        
        products = [
            {
                "id": product[0],
                "product_id": product[1],
                "product_name": product[2],
                "category": product[3],
                "sub_category": product[4],
                "sales": product[5]
            }
            for product in result
        ]
        
        return Response({"products": products}, status=status.HTTP_200_OK)
