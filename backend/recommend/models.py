from django.conf import settings
from django.db import models


class StockDna(models.Model):
    """종목 성격 점수 (정규화 캐시, 일배치). 궁합 계산은 이 테이블만 읽음."""

    stock = models.ForeignKey("stocks.Stock", on_delete=models.CASCADE, related_name="dna")
    volatility = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True, help_text="pct(beta)")
    value_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, help_text="pct(1/PBR)")
    growth_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, help_text="pct(net_profit_yoy)")
    stability = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, help_text="pct(1/beta)")
    sector = models.CharField(max_length=50, blank=True)
    calculated_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stock", "calculated_date"], name="stockdna_stock_date_unique"),
        ]

    def __str__(self):
        return f"DNA {self.stock_id} {self.calculated_date}"


class RecommendationCache(models.Model):
    """추천 결과 저장소 (궁합 + 장투 개인점수, TTL)."""

    class RecType(models.TextChoices):
        ONBOARDING = "onboarding", "온보딩 궁합"
        LONG_TERM = "long_term", "장투"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations"
    )
    stock = models.ForeignKey("stocks.Stock", on_delete=models.CASCADE, related_name="recommendations")
    rec_type = models.CharField(max_length=20, choices=RecType.choices, default=RecType.ONBOARDING)
    match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="0~100")
    rank = models.PositiveSmallIntegerField(null=True, blank=True)
    reason = models.JSONField(default=dict, help_text="요소별 기여 + 한줄요약")
    expires_at = models.DateTimeField(help_text="TTL: 하루 뒤 만료")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "stock", "rec_type"], name="reccache_user_stock_type_unique"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "rec_type", "rank"]),
        ]

    def __str__(self):
        return f"{self.user_id} {self.stock_id} {self.rec_type} {self.match_score}"


class LongTermScore(models.Model):
    """종목 장투 점수 (종목 단위 소계 = 재무+성장. 개인 궁합 30%는 RecommendationCache서 결합)."""

    stock = models.ForeignKey("stocks.Stock", on_delete=models.CASCADE, related_name="long_term_scores")
    financial_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    growth_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="종목 소계 (재무+성장)"
    )
    calculated_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stock", "calculated_date"], name="ltscore_stock_date_unique"),
        ]

    def __str__(self):
        return f"LT {self.stock_id} {self.total_score} {self.calculated_date}"


class UserLikedStock(models.Model):
    """찜한 종목 (워치리스트). 장투 재검증은 보유(Holding) 기준으로 이동 — 여기선 단순 북마크."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="liked_stocks"
    )
    stock = models.ForeignKey("stocks.Stock", on_delete=models.CASCADE, related_name="liked_by")
    liked_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "stock"], name="userlikedstock_user_stock_unique"),
        ]

    def __str__(self):
        return f"{self.user_id} likes {self.stock_id}"


class HoldingMilestone(models.Model):
    """보유 기념일 (30/90/180/365일 스냅샷)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="milestones"
    )
    stock = models.ForeignKey("stocks.Stock", on_delete=models.CASCADE, related_name="milestones")
    milestone_days = models.PositiveSmallIntegerField(help_text="30/90/180/365")
    snapshot = models.JSONField(default=dict, help_text="그 시점 지표")
    reached_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "stock", "milestone_days"], name="milestone_user_stock_days_unique"
            ),
        ]

    def __str__(self):
        return f"{self.user_id} {self.stock_id} {self.milestone_days}d"
