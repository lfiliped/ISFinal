from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Subclasse de GraphQLView que exenta CSRF
@method_decorator(csrf_exempt, name='dispatch')
class CSRFExemptGraphQLView(GraphQLView):
    pass

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', CSRFExemptGraphQLView.as_view(graphiql=True)),
]
