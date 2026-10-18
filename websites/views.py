from rest_framework.generics import ListAPIView

from websites.models import Website
from websites.serializers import WebsiteSerializer


class WebsiteListAPIView(ListAPIView):
    """GET /api/websites/ — active websites the user can select."""

    authentication_classes = []
    pagination_class = None
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        return Website.objects.filter(is_active=True).order_by("name", "id")
