from django.db import models


class Website(models.Model):
    name = models.CharField(max_length=150)

    base_url = models.URLField(max_length=500, unique=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
