from django.urls import path

from conversations.views import ConversationDetailAPIView, ConversationListAPIView

urlpatterns = [
    path("", ConversationListAPIView.as_view(), name="conversation-list"),
    path("<int:conversation_id>/", ConversationDetailAPIView.as_view(), name="conversation-detail"),
]
