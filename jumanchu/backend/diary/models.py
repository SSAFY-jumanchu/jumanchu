from django.conf import settings
from django.db import models


class StockDiary(models.Model):
    class ActionType(models.TextChoices):
        BUY = "BUY", "매수"
        SELL = "SELL", "매도"
        WATCH = "WATCH", "관심"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diaries"
    )
    stock = models.ForeignKey("stocks.Stock", on_delete=models.RESTRICT, related_name="diaries")
    order = models.ForeignKey(
        "portfolio.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diaries",
    )
    action_type = models.CharField(max_length=8, choices=ActionType.choices)
    reason_category = models.CharField(max_length=50, blank=True)
    reason_text = models.TextField()
    confidence = models.PositiveSmallIntegerField()
    target_price = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True
    )
    stop_loss_price = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True
    )
    related_news = models.ForeignKey(
        "stocks.StockNews",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diaries",
    )
    diary_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(confidence__gte=1) & models.Q(confidence__lte=5),
                name="diary_confidence_1_5",
            ),
            models.CheckConstraint(
                condition=models.Q(action_type__in=["BUY", "SELL", "WATCH"]),
                name="diary_action_type_enum",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-diary_date"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.user_id} {self.stock_id} {self.action_type} {self.diary_date}"


class DiaryReview(models.Model):
    diary = models.OneToOneField(
        StockDiary, on_delete=models.CASCADE, related_name="review"
    )
    actual_return = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    judgment = models.CharField(max_length=50, blank=True)
    lesson = models.TextField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"review of diary {self.diary_id}"
