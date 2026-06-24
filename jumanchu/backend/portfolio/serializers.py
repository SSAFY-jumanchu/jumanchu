from rest_framework import serializers

from accounts.models import Goal
from portfolio.models import Account, Holding, Order
from stocks.serializers import StockSerializer


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['user_id', 'balance', 'initial_balance', 'created_at', 'updated_at']


class HoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    total_invested = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    current_price = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    current_value = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    profit_loss = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    profit_loss_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Holding
        fields = ['stock', 'quantity', 'average_price', 'total_invested',
                  'current_price', 'current_value', 'profit_loss',
                  'profit_loss_rate', 'first_acquired_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    stock_code = serializers.CharField(source='stock.code', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    market = serializers.CharField(source='stock.market', read_only=True)
    currency = serializers.CharField(source='stock.currency', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'account', 'stock_code', 'stock_name',
                  'market', 'currency',
                  'side', 'quantity', 'price', 'total_amount',
                  'fee', 'tax', 'realized_pnl', 'status',
                  'idempotency_key', 'created_at', 'executed_at']


class OrderPreviewRequestSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    side = serializers.ChoiceField(choices=Order.Side.choices)
    quantity = serializers.IntegerField(min_value=1)


class OrderPreviewBodySerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    stock_name = serializers.CharField()
    side = serializers.ChoiceField(choices=Order.Side.choices)
    quantity = serializers.IntegerField()
    current_price = serializers.DecimalField(max_digits=18, decimal_places=4)
    estimated_total = serializers.DecimalField(max_digits=20, decimal_places=4)
    estimated_fee = serializers.DecimalField(max_digits=18, decimal_places=4)
    balance_after = serializers.DecimalField(max_digits=15, decimal_places=0)
    holding_after = HoldingSerializer(required=False, allow_null=True)
    avg_price_after = serializers.DecimalField(max_digits=18, decimal_places=4, required=False, allow_null=True)
    realized_profit = serializers.DecimalField(max_digits=20, decimal_places=4, required=False, allow_null=True)
    realized_profit_rate = serializers.FloatField(required=False, allow_null=True)


class OrderPreviewResponseSerializer(serializers.Serializer):
    is_valid = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField(), required=False)
    preview = OrderPreviewBodySerializer()


class OrderCreateRequestSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    side = serializers.ChoiceField(choices=Order.Side.choices)
    quantity = serializers.IntegerField(min_value=1)
    idempotency_key = serializers.CharField(max_length=64)


class OrderCreateResponseSerializer(serializers.Serializer):
    order = OrderSerializer()
    balance_after = serializers.DecimalField(max_digits=15, decimal_places=0)
    holding_after = HoldingSerializer(required=False, allow_null=True)


class OrderListResponseSerializer(serializers.Serializer):
    items = OrderSerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total = serializers.IntegerField()


class OrderDetailResponseSerializer(serializers.Serializer):
    order = OrderSerializer()
    stock = StockSerializer()
    related_diary_id = serializers.IntegerField(required=False, allow_null=True)


class PortfolioSummaryResponseSerializer(serializers.Serializer):
    account = AccountSerializer()
    total_invested = serializers.DecimalField(max_digits=20, decimal_places=4)
    total_current_value = serializers.DecimalField(max_digits=20, decimal_places=4)
    total_profit_loss = serializers.DecimalField(max_digits=20, decimal_places=4)
    total_profit_loss_rate = serializers.FloatField()
    total_assets = serializers.DecimalField(max_digits=20, decimal_places=4)
    holdings_count = serializers.IntegerField()
    holdings_preview = HoldingSerializer(many=True)
    generated_at = serializers.DateTimeField()


class HoldingsListResponseSerializer(serializers.Serializer):
    items = HoldingSerializer(many=True)
    total_count = serializers.IntegerField()
    total_invested = serializers.DecimalField(max_digits=20, decimal_places=4)
    total_current_value = serializers.DecimalField(max_digits=20, decimal_places=4)
    total_profit_loss = serializers.DecimalField(max_digits=20, decimal_places=4)
    generated_at = serializers.DateTimeField()


class HoldingReviewSerializer(serializers.Serializer):
    status = serializers.CharField(allow_blank=True)  # GREEN/YELLOW/RED, 판정불가는 ''
    violations = serializers.ListField(child=serializers.CharField())
    checked_at = serializers.DateTimeField(allow_null=True)


class HoldingDetailResponseSerializer(serializers.Serializer):
    holding = HoldingSerializer()
    transaction_count = serializers.IntegerField()
    recent_orders = OrderSerializer(many=True)
    related_diaries_count = serializers.IntegerField()
    review = HoldingReviewSerializer()


class BalanceResponseSerializer(serializers.Serializer):
    account = AccountSerializer()


class SectorAllocationSerializer(serializers.Serializer):
    sector = serializers.CharField()
    value = serializers.DecimalField(max_digits=20, decimal_places=4)
    rate = serializers.FloatField()


class StockAllocationSerializer(serializers.Serializer):
    stock_code = serializers.CharField()
    stock_name = serializers.CharField()
    value = serializers.DecimalField(max_digits=20, decimal_places=4)
    rate = serializers.FloatField()


class AllocationResponseSerializer(serializers.Serializer):
    total_value = serializers.DecimalField(max_digits=20, decimal_places=4)
    by_sector = SectorAllocationSerializer(many=True)
    by_stock = StockAllocationSerializer(many=True)
    cash_rate = serializers.FloatField()


class GoalSerializer(serializers.ModelSerializer):
    icon = serializers.CharField(source='badge_emoji')

    class Meta:
        model = Goal
        fields = ['id', 'name', 'target_amount', 'icon', 'description',
                  'category', 'tier', 'sort_order']


class MilestonesResponseSerializer(serializers.Serializer):
    current_profit = serializers.DecimalField(max_digits=20, decimal_places=4)
    achieved = GoalSerializer(many=True)
    next = GoalSerializer(allow_null=True)
    progress_percent = serializers.IntegerField()
    total_count = serializers.IntegerField()
