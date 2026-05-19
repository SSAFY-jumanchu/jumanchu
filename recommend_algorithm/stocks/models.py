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