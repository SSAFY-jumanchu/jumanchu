from django.db import models


class FeedNews(models.Model):
    """RSS 피드로 수집한 뉴스의 카테고리 메타.

    stocks.StockNews 를 변형하지 않고(=BE 모델 무수정) newses 도메인에서 카테고리를
    부여하기 위한 연결 테이블. 한 기사가 여러 피드(예: 경제+세계)에 동시 게재될 수
    있어 (news, category) 유니크로 다중 카테고리를 허용한다.
    """

    class Category(models.TextChoices):
        ECONOMY = "economy", "경제"
        POLITICS = "politics", "정치"
        WORLD = "world", "세계"

    news = models.ForeignKey(
        "stocks.StockNews", on_delete=models.CASCADE, related_name="feed_categories"
    )
    category = models.CharField(max_length=16, choices=Category.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["news", "category"], name="feednews_news_category_unique"
            ),
        ]
        indexes = [models.Index(fields=["category"])]

    def __str__(self):
        return f"{self.category}:{self.news_id}"


class NewsSector(models.Model):
    """뉴스 1건의 섹터 신호(정본 22). 엔티티(기업명) + 토픽(주제어) 매칭을 병합한
    뉴스→섹터 점수. 추천에서 사용자 preferred_sector 와 매칭하는 단일 소스다.
    (관련주가 없는 거시/지정학 뉴스도 섹터 신호를 남길 수 있음.)
    """

    news = models.ForeignKey(
        "stocks.StockNews", on_delete=models.CASCADE, related_name="sectors"
    )
    sector = models.CharField(max_length=50)            # 정본 22 섹터
    score = models.DecimalField(max_digits=4, decimal_places=3, default=0)  # 0~1

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["news", "sector"], name="newssector_news_sector_unique"
            ),
        ]
        indexes = [models.Index(fields=["sector"])]

    def __str__(self):
        return f"{self.sector}({self.score}):{self.news_id}"
