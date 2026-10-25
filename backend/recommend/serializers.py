from rest_framework import serializers


class WatchlistAddRequestSerializer(serializers.Serializer):
    stock_code = serializers.CharField()


class WatchlistItemSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    stock_name = serializers.CharField()
    market = serializers.CharField()
    sector = serializers.CharField(allow_blank=True)
    current_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    change_rate = serializers.FloatField(allow_null=True)
    liked_at = serializers.DateTimeField()
    is_active = serializers.BooleanField()


class WatchlistListResponseSerializer(serializers.Serializer):
    items = WatchlistItemSerializer(many=True)
    total = serializers.IntegerField()


class StockDnaScoreSerializer(serializers.Serializer):
    volatility = serializers.FloatField(allow_null=True)
    value_score = serializers.FloatField(allow_null=True)
    growth_score = serializers.FloatField(allow_null=True)
    stability = serializers.FloatField(allow_null=True)


class SwipeCardSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    stock_name = serializers.CharField()
    market = serializers.CharField()
    sector = serializers.CharField(allow_blank=True)
    match_score = serializers.FloatField()
    rank = serializers.IntegerField()
    dna = StockDnaScoreSerializer()
    reason = serializers.CharField()
    current_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    change_rate = serializers.FloatField(allow_null=True)
    like_count = serializers.IntegerField()


class SwipeRecommendResponseSerializer(serializers.Serializer):
    items = SwipeCardSerializer(many=True)
    total = serializers.IntegerField()
    generated_at = serializers.DateTimeField()
