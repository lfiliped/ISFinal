import graphene
from graphene_django.types import DjangoObjectType
from django.db import connection

# Define a query para cidades
class CityType(graphene.ObjectType):
    id = graphene.ID()
    nome = graphene.String()
    latitude = graphene.Float()
    longitude = graphene.Float()

class Query(graphene.ObjectType):
    cities = graphene.List(CityType, nome=graphene.String())

    def resolve_cities(self, info, nome=None):
        with connection.cursor() as cursor:
            if nome:
                cursor.execute("SELECT id, nome, latitude, longitude FROM cities WHERE nome ILIKE %s", [f"%{nome}%"])
            else:
                cursor.execute("SELECT id, nome, latitude, longitude FROM cities")
            result = cursor.fetchall()

        return [CityType(id=row[0], nome=row[1], latitude=row[2], longitude=row[3]) for row in result]

class Mutation(graphene.ObjectType):
    update_city = graphene.Field(CityType, id=graphene.ID(), latitude=graphene.Float(), longitude=graphene.Float())

    def resolve_update_city(self, info, id, latitude, longitude):
        with connection.cursor() as cursor:
            cursor.execute("UPDATE cities SET latitude=%s, longitude=%s WHERE id=%s", [latitude, longitude, id])
            cursor.execute("SELECT id, nome, latitude, longitude FROM cities WHERE id=%s", [id])
            result = cursor.fetchone()

        if result:
            return CityType(id=result[0], nome=result[1], latitude=result[2], longitude=result[3])

schema = graphene.Schema(query=Query, mutation=Mutation)
