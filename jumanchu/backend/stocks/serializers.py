from rest_framework import serializers

from stocks.models import (
    EconomicEvent,
    FinancialSummary,
    Stock,
    StockIndicator,
)


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['code', 'name', 'market', 'sector', 'industry',
                  'listed_at', 'market_cap', 'currency', 'kis_short_code',
                  'is_active', 'is_sp500', 'is_nasdaq100', 'updated_at']


class StockDetailSerializer(StockSerializer):
    description = serializers.CharField(required=False, allow_blank=True)
    homepage_url = serializers.URLField(required=False, allow_null=True)
    ceo_name = serializers.CharField(required=False, allow_blank=True)
    employee_count = serializers.IntegerField(required=False, allow_null=True)
    is_in_watchlist = serializers.BooleanField()

    class Meta(StockSerializer.Meta):
        fields = StockSerializer.Meta.fields + [
            'description', 'homepage_url', 'ceo_name',
            'employee_count', 'is_in_watchlist',
        ]


class StockListResponseSerializer(serializers.Serializer):
    items = StockSerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total = serializers.IntegerField()


class StockDetailResponseSerializer(serializers.Serializer):
    stock = StockDetailSerializer()


class StockWarningsSerializer(serializers.Serializer):
    is_management = serializers.BooleanField()
    is_short_overheated = serializers.BooleanField()
    is_trading_halted = serializers.BooleanField()
    is_vi_active = serializers.BooleanField()
    short_term_overheated = serializers.BooleanField()
    investment_caution = serializers.BooleanField()
    warning_label = serializers.CharField(required=False, allow_null=True)


class StockPriceSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    current = serializers.DecimalField(max_digits=18, decimal_places=4)
    open = serializers.DecimalField(max_digits=18, decimal_places=4)
    high = serializers.DecimalField(max_digits=18, decimal_places=4)
    low = serializers.DecimalField(max_digits=18, decimal_places=4)
    prev_close = serializers.DecimalField(max_digits=18, decimal_places=4)
    change = serializers.DecimalField(max_digits=18, decimal_places=4)
    change_rate = serializers.FloatField()
    volume = serializers.IntegerField()
    trading_value = serializers.DecimalField(max_digits=20, decimal_places=4)
    upper_limit = serializers.DecimalField(max_digits=18, decimal_places=4)
    lower_limit = serializers.DecimalField(max_digits=18, decimal_places=4)
    warnings = StockWarningsSerializer()
    fetched_at = serializers.DateTimeField()


class StockPriceResponseSerializer(serializers.Serializer):
    price = StockPriceSerializer()


class OrderBookEntrySerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=18, decimal_places=4)
    quantity = serializers.IntegerField()


class OrderBookSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    asks = OrderBookEntrySerializer(many=True)
    bids = OrderBookEntrySerializer(many=True)
    total_ask_quantity = serializers.IntegerField()
    total_bid_quantity = serializers.IntegerField()
    is_market_open = serializers.BooleanField()  # false + 빈 배열 = 장 마감, true + 빈 배열 = 호가 없음
    fetched_at = serializers.DateTimeField()


class OrderBookResponseSerializer(serializers.Serializer):
    orderbook = OrderBookSerializer()


class CandleSerializer(serializers.Serializer):
    time = serializers.DateTimeField()
    open = serializers.DecimalField(max_digits=18, decimal_places=4)
    high = serializers.DecimalField(max_digits=18, decimal_places=4)
    low = serializers.DecimalField(max_digits=18, decimal_places=4)
    close = serializers.DecimalField(max_digits=18, decimal_places=4)
    volume = serializers.IntegerField()


class ChartResponseSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    period = serializers.CharField()
    interval = serializers.CharField()
    candles = CandleSerializer(many=True)
    generated_at = serializers.DateTimeField()


class FinancialSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialSummary
        fields = ['fiscal_period', 'revenue', 'operating_profit', 'net_profit',
                  'operating_margin', 'net_margin',
                  'revenue_yoy', 'operating_profit_yoy', 'net_profit_yoy',
                  'debt_ratio', 'equity_ratio', 'current_ratio', 'payout_ratio',
                  'data_source', 'fetched_at']


class StockIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockIndicator
        fields = ['per', 'pbr', 'eps', 'roe', 'roa', 'dividend_yield',
                  'beta', 'volatility', 'high_52w', 'low_52w', 'calculated_date']


class FinancialsResponseSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    type = serializers.ChoiceField(choices=['quarterly', 'annual'])
    summaries = FinancialSummarySerializer(many=True)
    indicator = StockIndicatorSerializer()
    last_updated = serializers.DateTimeField()


class PostSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    author_nickname = serializers.CharField(source='user.nickname')
    created_at = serializers.DateTimeField()
    comment_count = serializers.IntegerField()
    like_count = serializers.IntegerField()


class StockPostsResponseSerializer(serializers.Serializer):
    items = PostSummarySerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total = serializers.IntegerField()


class IndexSummarySerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    current = serializers.FloatField()
    change = serializers.FloatField()
    change_rate = serializers.FloatField()


class StockSummarySerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    current = serializers.DecimalField(max_digits=18, decimal_places=4)
    change = serializers.DecimalField(max_digits=18, decimal_places=4)
    change_rate = serializers.FloatField()


class MarketRankingsSerializer(serializers.Serializer):
    top_gainers = StockSummarySerializer(many=True)
    top_losers = StockSummarySerializer(many=True)
    most_active = StockSummarySerializer(many=True)


class MarketSummaryResponseSerializer(serializers.Serializer):
    indices = IndexSummarySerializer(many=True)
    kr = MarketRankingsSerializer()
    us = MarketRankingsSerializer()
    fetched_at = serializers.DateTimeField()


class PopularStockSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    market = serializers.CharField()
    current = serializers.DecimalField(max_digits=18, decimal_places=4)
    change = serializers.DecimalField(max_digits=18, decimal_places=4)
    change_rate = serializers.FloatField()
    trading_value = serializers.DecimalField(max_digits=24, decimal_places=4, allow_null=True)       # 원본 통화
    trading_value_krw = serializers.DecimalField(max_digits=24, decimal_places=4, allow_null=True)   # 정렬용 KRW 환산
    volume = serializers.IntegerField(allow_null=True)
    # 거래비율(체결강도) — 워밍 캐시. 워밍 전/실패면 null
    volume_power = serializers.FloatField(allow_null=True, required=False)   # 체결강도(매수/매도×100)
    buy_ratio = serializers.FloatField(allow_null=True, required=False)      # 매수 체결 %
    sell_ratio = serializers.FloatField(allow_null=True, required=False)     # 매도 체결 %


class PopularRankingResponseSerializer(serializers.Serializer):
    items = PopularStockSerializer(many=True)
    market = serializers.ChoiceField(choices=['all', 'domestic', 'overseas'])
    sort = serializers.ChoiceField(choices=['value', 'volume', 'up', 'down'])
    fetched_at = serializers.DateTimeField()


class EconomicEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EconomicEvent
        fields = ['id', 'event_date', 'title', 'importance', 'country']


class EconomicEventListResponseSerializer(serializers.Serializer):
    items = EconomicEventSerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total = serializers.IntegerField()
