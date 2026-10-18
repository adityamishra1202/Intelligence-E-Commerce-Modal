from rest_framework.response import Response
from rest_framework.views import APIView

from conversations.models import Conversation
from conversations.serializers import ConversationDetailSerializer, ConversationSummarySerializer

LIST_LIMIT = 50


def _owner_key(request):
    # Reading never creates a session: a browser without one owns nothing.
    return request.session.session_key


class ConversationListAPIView(APIView):
    """GET /api/conversations/ — this browser's newest 50 conversations."""

    authentication_classes = []

    def get(self, request):
        owner_key = _owner_key(request)
        if not owner_key:
            return Response([])
        conversations = Conversation.objects.filter(owner_key=owner_key).order_by("-updated_at", "-id")
        return Response(ConversationSummarySerializer(conversations[:LIST_LIMIT], many=True).data)


class ConversationDetailAPIView(APIView):
    """GET /api/conversations/<id>/ — 404 unless this browser owns it (never 403)."""

    authentication_classes = []

    def get(self, request, conversation_id):
        owner_key = _owner_key(request)
        conversation = (
            Conversation.objects.filter(id=conversation_id, owner_key=owner_key).first() if owner_key else None
        )
        if conversation is None:
            return Response({"error": "Conversation not found.", "code": "conversation_not_found"}, status=404)
        return Response(ConversationDetailSerializer(conversation).data)
