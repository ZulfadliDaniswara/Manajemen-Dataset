from rest_framework import serializers
from .models import ExternalMessage

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalMessage
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']