from rest_framework import serializers


class NaverArticleSerializer(serializers.Serializer):
    title = serializers.CharField()
    url = serializers.CharField()
    # published_at 은 naver_news.to_dict() 에서 ISO 문자열 또는 None 으로 옴
    published_at = serializers.CharField(allow_null=True)
    summary = serializers.CharField(allow_blank=True)
    body = serializers.CharField(allow_blank=True)


class NewsListResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    count = serializers.IntegerField()
    items = NaverArticleSerializer(many=True)


class StockBriefSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    market = serializers.CharField()
    sector = serializers.CharField(allow_blank=True)


class StockNewsResponseSerializer(serializers.Serializer):
    stock = StockBriefSerializer()
    count = serializers.IntegerField()
    items = NaverArticleSerializer(many=True)


class RelatedStockSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    sector = serializers.CharField(allow_blank=True)
    relevance_score = serializers.FloatField()


class SectorSignalSerializer(serializers.Serializer):
    sector = serializers.CharField()
    score = serializers.FloatField()


class FeedNewsItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    url = serializers.CharField()
    source = serializers.CharField(allow_blank=True)
    published_at = serializers.CharField(allow_null=True)
    categories = serializers.ListField(child=serializers.CharField())
    related_stocks = RelatedStockSerializer(many=True)
    sectors = SectorSignalSerializer(many=True)


class FeedNewsResponseSerializer(serializers.Serializer):
    category = serializers.CharField(allow_null=True, required=False)
    sector = serializers.CharField(allow_null=True, required=False)
    count = serializers.IntegerField()
    items = FeedNewsItemSerializer(many=True)
