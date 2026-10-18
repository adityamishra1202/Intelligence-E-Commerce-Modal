from django.urls import path

from websites.views import WebsiteListAPIView

urlpatterns = [
    path("", WebsiteListAPIView.as_view(), name="website-list"),
]
