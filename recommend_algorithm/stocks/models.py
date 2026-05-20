from django.db import models

class Stock(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    market_cap = models.BigIntegerField(null=True)

    per = models.FloatField(null=True)
    pbr = models.FloatField(null=True)
    eps = models.FloatField(null=True)
    bps = models.FloatField(null=True)
    beta = models.FloatField(null=True)
    is_valid = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class InvalidStock(models.Model): #가져온 데이터 이상있는 항복 일단 따로저장
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    market_cap = models.BigIntegerField(null=True)

    per = models.FloatField(null=True)
    pbr = models.FloatField(null=True)
    eps = models.FloatField(null=True)
    bps = models.FloatField(null=True)
    beta = models.FloatField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

class PrototypePool(models.Model):
    # Stock과 1:1 관계 유지 (primary_key=True이므로 이 필드가 PK 역할을 합니다)
    stock = models.OneToOneField(
        'Stock',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='prototype_pool'
    )

    # ── Stock 테이블과 동일한 컬럼 순서 유지 ──────────────────────────────
    code = models.CharField(max_length=10, db_index=True, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    per = models.FloatField(null=True, blank=True)
    pbr = models.FloatField(null=True, blank=True)
    eps = models.FloatField(null=True, blank=True)
    bps = models.FloatField(null=True, blank=True)
    beta = models.FloatField(null=True, blank=True)

    # ── PrototypePool 전용 필드 ────────────────────────────────────────────
    rank = models.IntegerField(help_text="시가총액 순위 (1~200)")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-market_cap']
        # Admin 페이지 등에서 단수/복수형 이름이 예쁘게 나오도록 추가
        verbose_name = "프로토타입 풀 종목"
        verbose_name_plural = "프로토타입 풀 종목들"

    def __str__(self):
        return f"[{self.rank}위] {self.name} ({self.code})"