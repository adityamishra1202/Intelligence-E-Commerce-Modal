from django.db import models


class Conversation(models.Model):
    title = models.CharField(
        max_length=200,
        default="New conversation"
    )

    website_scope = models.JSONField(
        default=list
    )

    current_requirements = models.JSONField(
        default=dict,
        blank=True
    )

    # Session key of the browser that created the conversation. Lookups are
    # filtered by it; rows created before ownership existed keep '' and are
    # reachable only through the Django admin.
    owner_key = models.CharField(
        max_length=64,
        db_index=True,
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title
class Message(models.Model):

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"    
