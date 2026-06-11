from django.conf import settings
from django.db import models


class Account(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account"
    )
    balance = models.DecimalField(max_digits=15, decimal_places=0, default=100_000_000)
    initial_balance = models.DecimalField(max_digits=15, decimal_places=0, default=100_000_000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(balance__gte=0), name="account_balance_nonneg"),
        ]

    def __str__(self):
        return f"{self.user_id} balance={self.balance}"


class Holding(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holdings"
    )
    stock = models.ForeignKey("stocks.Stock", on_delete=models.RESTRICT, related_name="holdings")
    quantity = models.PositiveIntegerField(default=0)
    average_price = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    first_acquired_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "stock"], name="holding_user_stock_unique"),
            models.CheckConstraint(condition=models.Q(quantity__gte=0), name="holding_quantity_nonneg"),
        ]

    def __str__(self):
        return f"{self.user_id} {self.stock_id} x{self.quantity}"


class Order(models.Model):
    class Side(models.TextChoices):
        BUY = "BUY", "매수"
        SELL = "SELL", "매도"

    class Status(models.TextChoices):
        PENDING = "PENDING", "대기"
        FILLED = "FILLED", "체결"
        FAILED = "FAILED", "실패"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
    )
    account = models.ForeignKey(Account, on_delete=models.RESTRICT, related_name="orders")
    stock = models.ForeignKey("stocks.Stock", on_delete=models.RESTRICT, related_name="orders")
    side = models.CharField(max_length=8, choices=Side.choices)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=18, decimal_places=4)
    total_amount = models.DecimalField(max_digits=20, decimal_places=4)
    fee = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    realized_pnl = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="매도 실현손익 = (체결가-평균매입가)×수량, 매수는 NULL",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="order_quantity_pos"),
            models.CheckConstraint(condition=models.Q(price__gt=0), name="order_price_pos"),
            models.CheckConstraint(condition=models.Q(total_amount__gt=0), name="order_total_pos"),
            models.CheckConstraint(condition=models.Q(side__in=["BUY", "SELL"]), name="order_side_enum"),
            models.CheckConstraint(
                condition=models.Q(status__in=["PENDING", "FILLED", "FAILED"]),
                name="order_status_enum",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["account", "status"]),
            models.Index(fields=["stock", "-executed_at"]),
        ]

    def __str__(self):
        return f"{self.side} {self.stock_id} x{self.quantity} @ {self.price}"
