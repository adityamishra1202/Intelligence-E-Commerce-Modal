from django.urls import path

from assistant.views import ChatAPIView

urlpatterns = [
    path("chat/", ChatAPIView.as_view(), name="chat"),
]