from rest_framework import serializers
from .models import ExternalMessage, ReplyMessage

class MessageInboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalMessage
        fields = ['id', 'project_name', 'sender', 'status', 'timestamp']

class MessageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalMessage
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']

class ReplyMessageSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='original_message.project_name', read_only=True)

    class Meta:
        model = ReplyMessage
        # === TAMBAHKAN 'dataset_link' DI SINI ===
        fields = ['project_name', 'message_text', 'dataset_link', 'created_at']