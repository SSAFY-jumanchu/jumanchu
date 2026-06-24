from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nickname = models.CharField(max_length=20, unique=True)
    birth_year = models.PositiveSmallIntegerField()

    REQUIRED_FIELDS = ['email', 'nickname', 'birth_year']

    def __str__(self):
        return f"{self.username} ({self.nickname})"




class InvestmentProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="investment_profile"
    )
    investment_style = models.CharField(
        max_length=50,
        blank=True,
        help_text="성향 4유형 라벨(가치 파트너형/성장 동반형/단기 승부형/신중 탐색형). 5벡터에서 산출해 저장",
    )
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
        return f"{self.user.username} · {self.investment_style}"


class Goal(models.Model):
    """목표 마스터 — 시스템 시드(모든 유저 공통). 누적수익 목표 + 달성 뱃지."""

    name = models.CharField(max_length=100)
    target_amount = models.BigIntegerField(help_text="누적 수익(총자산-초기지급금) 목표 금액")
    badge_emoji = models.CharField(max_length=8)
    badge_name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, help_text="달성 시 한 줄 멘트")
    category = models.CharField(
        max_length=20, blank=True,
        help_text="electronics/luxury/travel/car/realestate/life",
    )
    tier = models.PositiveSmallIntegerField(null=True, blank=True, help_text="구간 1~5 (그룹핑용)")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class UserGoal(models.Model):
    """유저별 목표 달성 기록 = 뱃지 획득 (닉네임 옆 표시)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="achievements")
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "goal"], name="usergoal_user_goal_unique"),
        ]

    def __str__(self):
        return f"{self.user_id} achieved {self.goal_id}"


class UserPreferredSector(models.Model):
    """복수 관심 섹터 (1순위 1.0 / 2순위 0.6 / 3순위 0.3)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preferred_sectors")
    sector = models.CharField(max_length=50)
    weight = models.DecimalField(max_digits=4, decimal_places=2, help_text="순위 가중치")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sector"], name="userpreferredsector_user_sector_unique"
            ),
        ]

    def __str__(self):
        return f"{self.user_id} {self.sector}"
