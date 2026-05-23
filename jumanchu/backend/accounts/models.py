from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nickname = models.CharField(max_length=20, unique=True)
    birth_year = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.username} ({self.nickname})"


class InvestmentProfile(models.Model):
    class RiskType(models.TextChoices):
        CONSERVATIVE = "CONSERVATIVE", "안정형"
        MODERATE = "MODERATE", "중립형"
        AGGRESSIVE = "AGGRESSIVE", "공격형"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="investment_profile"
    )
    risk_type = models.CharField(max_length=16, choices=RiskType.choices)
    investment_style = models.CharField(max_length=50, blank=True)
    preferred_period = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="선호 보유 기간(개월). 예: 1, 3, 6, 12, 24",
    )
    preferred_sector = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} · {self.risk_type}"
