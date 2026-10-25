from rest_framework import serializers

from diary.models import StockDiary


class StockDiarySerializer(serializers.ModelSerializer):
    """일기 응답(읽기)."""

    stock_code = serializers.CharField(source='stock.code', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    order_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockDiary
        fields = ['id', 'stock_code', 'stock_name', 'order_id', 'action_type',
                  'reason_category', 'confidence', 'target_price',
                  'stop_loss_price', 'memo', 'created_at', 'updated_at']


class StockDiaryWriteSerializer(serializers.Serializer):
    """일기 작성/수정 입력. 종목은 stock_code, 주문은 order_id로 받는다."""

    stock_code = serializers.CharField()
    order_id = serializers.IntegerField(required=False, allow_null=True)
    action_type = serializers.ChoiceField(choices=StockDiary.ActionType.choices)
    reason_category = serializers.ChoiceField(
        choices=StockDiary.ReasonCategory.choices, required=False, allow_blank=True
    )
    confidence = serializers.IntegerField(min_value=1, max_value=5)
    target_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, required=False, allow_null=True
    )
    stop_loss_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, required=False, allow_null=True
    )
    memo = serializers.CharField(required=False, allow_blank=True)


class DiaryListResponseSerializer(serializers.Serializer):
    items = StockDiarySerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total = serializers.IntegerField()
