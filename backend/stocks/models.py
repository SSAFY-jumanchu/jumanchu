from django.db import models


class Stock(models.Model):
    class Market(models.TextChoices):
        KOSPI = "KOSPI", "코스피"
        KOSDAQ = "KOSDAQ", "코스닥"
        NASDAQ = "NASDAQ", "나스닥"
        NYSE = "NYSE", "뉴욕증권거래소"

    class Currency(models.TextChoices):
        KRW = "KRW", "원"
        USD = "USD", "달러"

    code = models.CharField(max_length=16)
    name = models.CharField(max_length=100)
    market = models.CharField(max_length=16, choices=Market.choices)
    sector = models.CharField(max_length=50, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    listed_at = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=8, choices=Currency.choices)
    kis_short_code = models.CharField(max_length=32, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_sp500 = models.BooleanField(default=False)
    is_nasdaq100 = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    homepage_url = models.URLField(max_length=200, null=True, blank=True)
    ceo_name = models.CharField(max_length=100, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code", "market"], name="stock_code_market_unique"),
        ]
        indexes = [
            models.Index(fields=["market", "is_active"]),
            models.Index(fields=["is_sp500"]),
            models.Index(fields=["is_nasdaq100"]),
        ]

    def __str__(self):
        return f"{self.code} {self.name}"


class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name="prices")
    price_date = models.DateField()
    open = models.DecimalField(max_digits=18, decimal_places=4)
    high = models.DecimalField(max_digits=18, decimal_places=4)
    low = models.DecimalField(max_digits=18, decimal_places=4)
    close = models.DecimalField(max_digits=18, decimal_places=4)
    volume = models.BigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stock", "price_date"], name="stockprice_stock_date_unique"),
        ]

    def __str__(self):
        return f"{self.stock.code} {self.price_date}"


class StockIndicator(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name="indicators")
    per = models.FloatField(null=True, blank=True)
    pbr = models.FloatField(null=True, blank=True)
    eps = models.IntegerField(null=True, blank=True)
    roe = models.FloatField(null=True, blank=True)
    roa = models.FloatField(null=True, blank=True)
    dividend_yield = models.FloatField(null=True, blank=True)
    beta = models.FloatField(null=True, blank=True)
    volatility = models.FloatField(null=True, blank=True)
    high_52w = models.IntegerField(null=True, blank=True)
    low_52w = models.IntegerField(null=True, blank=True)
    calculated_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["stock", "calculated_date"], name="stockindicator_stock_date_unique"
            ),
        ]

    def __str__(self):
        return f"{self.stock.code} indicator {self.calculated_date}"


class FinancialSummary(models.Model):
    class DataSource(models.TextChoices):
        DART = "DART", "DART"
        YFINANCE = "yfinance", "yfinance"

    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name="financials")
    fiscal_period = models.CharField(max_length=16)
    revenue = models.BigIntegerField(null=True, blank=True)
    operating_profit = models.BigIntegerField(null=True, blank=True)
    net_profit = models.BigIntegerField(null=True, blank=True)
    operating_margin = models.FloatField(null=True, blank=True)
    net_margin = models.FloatField(null=True, blank=True)
    revenue_yoy = models.FloatField(null=True, blank=True)
    operating_profit_yoy = models.FloatField(null=True, blank=True)
    net_profit_yoy = models.FloatField(null=True, blank=True)
    debt_ratio = models.FloatField(null=True, blank=True)
    equity_ratio = models.FloatField(null=True, blank=True)
    current_ratio = models.FloatField(null=True, blank=True)
    payout_ratio = models.FloatField(null=True, blank=True)
    data_source = models.CharField(max_length=16, choices=DataSource.choices)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["stock", "fiscal_period"], name="financialsummary_stock_period_unique"
            ),
        ]

    def __str__(self):
        return f"{self.stock.code} {self.fiscal_period}"


class StockNews(models.Model):
    title = models.CharField(max_length=300)
    url = models.URLField(max_length=500, unique=True)
    source = models.CharField(max_length=50, blank=True)
    published_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["-published_at"]),
        ]

    def __str__(self):
        return self.title[:50]


class NewsRelatedStock(models.Model):
    news = models.ForeignKey(StockNews, on_delete=models.CASCADE, related_name="related_stocks")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="related_news")
    relevance_score = models.DecimalField(
        max_digits=4, decimal_places=3, default=1, help_text="매칭 신뢰도(제목매칭 1.0 등)·정렬용"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["news", "stock"], name="newsrelatedstock_unique"),
        ]
        indexes = [
            models.Index(fields=["stock"]),
        ]


class EconomicEvent(models.Model):
    class Country(models.TextChoices):
        US = "US", "미국"
        KR = "KR", "한국"

    class Importance(models.TextChoices):
        HIGH = "HIGH", "상"
        MEDIUM = "MEDIUM", "중"
        LOW = "LOW", "하"

    event_date = models.DateField()
    title = models.CharField(max_length=120)
    importance = models.CharField(
        max_length=8, choices=Importance.choices, default=Importance.MEDIUM
    )
    country = models.CharField(max_length=4, choices=Country.choices)

    class Meta:
        ordering = ["event_date", "id"]
        indexes = [
            models.Index(fields=["event_date"]),
            models.Index(fields=["country", "event_date"]),
        ]

    def __str__(self):
        return f"[{self.country}] {self.event_date} {self.title}"
