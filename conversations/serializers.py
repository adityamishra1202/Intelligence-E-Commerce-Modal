from rest_framework import serializers

from conversations.models import Conversation, Message


class ConversationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "title", "website_scope", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["role", "content", "created_at"]


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "website_scope", "messages"]

    def get_messages(self, conversation):
        messages = conversation.messages.order_by("created_at", "id")
        return MessageSerializer(messages, many=True).data
