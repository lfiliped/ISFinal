from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)   
    schema_file = serializers.FileField(required=False)  
