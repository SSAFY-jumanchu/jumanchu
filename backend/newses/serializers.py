from rest_framework import serializers


class NaverArticleSerializer(serializers.Serializer):
    title = serializers.CharField()
    url = serializers.CharField()
    source = serializers.CharField(allow_blank=True, required=False, default='')  # 언론사명
    # published_at 은 naver_news.to_dict() 에서 ISO 문자열 또는 None 으로 옴
    published_at = serializers.CharField(allow_null=True)
    summary = serializers.CharField(allow_blank=True)             # 네이버 description 스니펫
    # 기사 본문(news.naver.com 호스팅분, 최대 2000자). content=true 일 때만 채워짐.
    content = serializers.CharField(source='body', allow_blank=True, required=False, default='')


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


class NewsStockBadgeSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()


class StockNewsFeedItemSerializer(serializers.Serializer):
    """관심/보유 종목 뉴스 카드 1개 (종목 배지 + 기사)."""
    stock = NewsStockBadgeSerializer()
    title = serializers.CharField()
    url = serializers.CharField()
    source = serializers.CharField(allow_blank=True)
    published_at = serializers.CharField(allow_null=True)
    summary = serializers.CharField(allow_blank=True)


class StockNewsFeedResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    items = StockNewsFeedItemSerializer(many=True)
