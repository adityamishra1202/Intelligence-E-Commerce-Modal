from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from .models import Product
from .serializers import ProductSerializer


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Start with an empty result set unless a website is selected.
        queryset = Product.objects.none()

        website_id = self.request.query_params.get("website_id")

        # Require an explicit website to prevent cross-website mixing.
        if not website_id:
            raise ValidationError({
                "website_id": "This parameter is required."
            })

        if not website_id.isdigit():
            raise ValidationError({
                "website_id": "Must be a valid positive integer."
            })

        queryset = Product.objects.filter(
            website_id=int(website_id),
            website__is_active=True,
        ).select_related("website")

        # Search by product title or description.
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
            )

        # Filter by category.
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(
                category__iexact=category
            )

        # Filter by maximum price.
        max_price = self.request.query_params.get("max_price")
        if max_price is not None:
            try:
                price = Decimal(max_price)
                if not price.is_finite() or price < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ValidationError({
                    "max_price": "Enter a valid non-negative price."
                })

            queryset = queryset.filter(price__lte=price)

        # Filter by minimum price.
        min_price = self.request.query_params.get("min_price")
        if min_price is not None:
            try:
                price = Decimal(min_price)
                if not price.is_finite() or price < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ValidationError({
                    "min_price": "Enter a valid non-negative price."
                })

            queryset = queryset.filter(price__gte=price)

        # Reject an inverted price range.
        if (
            min_price is not None
            and max_price is not None
            and Decimal(min_price) > Decimal(max_price)
        ):
            raise ValidationError({
                "price": "min_price cannot exceed max_price."
            })

        # Filter by minimum rating.
        min_rating = self.request.query_params.get("min_rating")
        if min_rating is not None:
            try:
                rating = Decimal(min_rating)
                if not rating.is_finite() or not Decimal("0") <= rating <= Decimal("5"):
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ValidationError({
                    "min_rating": "Enter a rating between 0 and 5."
                })

            queryset = queryset.filter(rating__gte=rating)

        # Filter by availability.
        available = self.request.query_params.get("available")
        if available is not None:
            if available.lower() not in ("true", "false"):
                raise ValidationError({
                    "available": "Use true or false."
                })

            queryset = queryset.filter(
                is_available=(available.lower() == "true")
            )

        # Restrict ordering to approved fields.
        ordering = self.request.query_params.get(
            "ordering", "title"
        )

        allowed_ordering = {
            "title",
            "-title",
            "price",
            "-price",
            "rating",
            "-rating",
        }

        if ordering not in allowed_ordering:
            raise ValidationError({
                "ordering": (
                    "Invalid ordering. Use title, -title, price, "
                    "-price, rating, or -rating."
                )
            })

        return queryset.order_by(ordering, "id")