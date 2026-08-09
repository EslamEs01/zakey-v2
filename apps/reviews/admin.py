"""Review moderation (FR-091, FR-094)."""

from __future__ import annotations

from django.contrib import admin
from django.utils import timezone

from .models import Review, ReviewStatus


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "author_name", "rating", "status", "is_verified_purchase", "created_at")
    list_filter = ("status", "rating", "is_verified_purchase")
    search_fields = ("product__name", "author_name", "body")
    date_hierarchy = "created_at"
    autocomplete_fields = ("product",)
    # Aggregates and verification are system-maintained (FR-094).
    readonly_fields = ("is_verified_purchase", "moderated_by", "moderated_at", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "customer")

    def _moderate(self, request, queryset, status):
        updated = 0
        for review in queryset:
            review.status = status
            review.moderated_by = request.user
            review.moderated_at = timezone.now()
            review.save(update_fields=["status", "moderated_by", "moderated_at", "updated_at"])
            recompute_product_rating(review.product)
            updated += 1
        self.message_user(request, f"تمت مراجعة {updated} تقييمًا.")

    @admin.action(description="اعتماد التقييمات المختارة")
    def approve(self, request, queryset):
        self._moderate(request, queryset, ReviewStatus.APPROVED)

    @admin.action(description="رفض التقييمات المختارة")
    def reject(self, request, queryset):
        self._moderate(request, queryset, ReviewStatus.REJECTED)

    actions = ("approve", "reject")


def recompute_product_rating(product) -> None:
    """Maintain the product aggregate from approved reviews only (FR-094)."""
    from decimal import Decimal

    from django.db.models import Avg, Count

    stats = product.reviews.filter(status=ReviewStatus.APPROVED).aggregate(
        average=Avg("rating"), total=Count("id")
    )
    product.rating_average = Decimal(str(round(stats["average"] or 0, 2)))
    product.review_count = stats["total"] or 0
    product.save(update_fields=["rating_average", "review_count", "updated_at"])
