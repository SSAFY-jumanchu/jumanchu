from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nickname = models.CharField(max_length=20, unique=True)
    birth_year = models.PositiveSmallIntegerField()

    REQUIRED_FIELDS = ['email', 'nickname', 'birth_year']

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
    # --- 온보딩 5벡터 (1~5, 온보딩 완료 시 채움) ---
    risk_tolerance = models.PositiveSmallIntegerField(null=True, blank=True, help_text="리스크 감수 1~5")
    investment_term = models.PositiveSmallIntegerField(null=True, blank=True, help_text="투자 기간 1~5")
    experience = models.PositiveSmallIntegerField(null=True, blank=True, help_text="투자 경험 1~5")
    loss_aversion = models.PositiveSmallIntegerField(null=True, blank=True, help_text="손실 회피 1~5")
    behavior = models.PositiveSmallIntegerField(null=True, blank=True, help_text="투자 스타일 1~5")
    onboarding_answers = models.JSONField(null=True, blank=True, help_text="온보딩 8문항 원답")
    profiled_at = models.DateTimeField(null=True, blank=True, help_text="프로파일링 완료 시각")
    signature_stock = models.ForeignKey(
        "stocks.Stock",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signature_profiles",
        help_text="가입 시점 궁합 1등 종목 박제 (OO형 투자자)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(risk_tolerance__isnull=True)
                | (models.Q(risk_tolerance__gte=1) & models.Q(risk_tolerance__lte=5)),
                name="profile_risk_tolerance_1_5",
            ),
            models.CheckConstraint(
                condition=models.Q(investment_term__isnull=True)
                | (models.Q(investment_term__gte=1) & models.Q(investment_term__lte=5)),
                name="profile_investment_term_1_5",
            ),
            models.CheckConstraint(
                condition=models.Q(experience__isnull=True)
                | (models.Q(experience__gte=1) & models.Q(experience__lte=5)),
                name="profile_experience_1_5",
            ),
            models.CheckConstraint(
                condition=models.Q(loss_aversion__isnull=True)
                | (models.Q(loss_aversion__gte=1) & models.Q(loss_aversion__lte=5)),
                name="profile_loss_aversion_1_5",
            ),
            models.CheckConstraint(
                condition=models.Q(behavior__isnull=True)
                | (models.Q(behavior__gte=1) & models.Q(behavior__lte=5)),
                name="profile_behavior_1_5",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.risk_type}"
