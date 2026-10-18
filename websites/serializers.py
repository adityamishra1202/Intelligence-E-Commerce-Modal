from rest_framework import serializers

from websites.models import Website


class WebsiteSerializer(serializers.ModelSerializer):
    stale = serializers.SerializerMethodField()

    class Meta:
        model = Website
        fields = ["id", "name", "base_url", "default_currency", "last_synced_at", "stale"]

    def get_stale(self, website):
        return website.is_stale()
