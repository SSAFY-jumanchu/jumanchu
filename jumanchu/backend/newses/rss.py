"""RSS 피드 수집·파싱 (연합뉴스TV 경제 등).

stdlib(`xml.etree`)만 사용 — 피드가 정형 RSS 2.0 1개라 충분. 매체가 여러 개로
늘면 그때 `feedparser` 도입 검토. 날짜(RFC822)·HTML 정제는 naver_news 헬퍼 재사용.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from urllib.request import Request, urlopen

from newses.naver_news import _clean, _parse_dt

# RSS 확장 네임스페이스
_NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
_UA = "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0)"

# 내부 카테고리 → 피드 URL (연합뉴스TV 패턴: /category/news/<slug>/feed/)
# 주의: '세계'는 연합뉴스 슬러그가 international (world 슬러그는 비정상 응답).
FEEDS: dict[str, str] = {
    "economy": "http://www.yonhapnewstv.co.kr/category/news/economy/feed/",
    "politics": "http://www.yonhapnewstv.co.kr/category/news/politics/feed/",
    "world": "http://www.yonhapnewstv.co.kr/category/news/international/feed/",
}
DEFAULT_SOURCE = "연합뉴스TV"


@dataclass(frozen=True)
class FeedArticle:
    title: str
    url: str
    published_at: datetime | None
    summary: str             # description(요약 스니펫)
    body: str                # content:encoded(본문) — 표시/신호용, 영구저장 지양
    author: str
    source: str
    category: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "body": self.body,
            "author": self.author,
            "source": self.source,
            "category": self.category,
        }


def _get(url: str, timeout: int = 12) -> bytes:
    req = Request(url, headers={"User-Agent": _UA})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_feed(xml_bytes: bytes, *, source: str = DEFAULT_SOURCE) -> list[FeedArticle]:
    """RSS 바이트 → FeedArticle 리스트 (네트워크 분리: 테스트 용이)."""
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return []
    out: list[FeedArticle] = []
    for it in channel.findall("item"):
        out.append(FeedArticle(
            title=_clean(it.findtext("title", "") or ""),
            url=(it.findtext("link", "") or "").strip(),
            published_at=_parse_dt(it.findtext("pubDate", "") or ""),
            summary=_clean(it.findtext("description", "") or ""),
            body=_clean(it.findtext("content:encoded", "", _NS) or ""),
            author=_clean(it.findtext("dc:creator", "", _NS) or ""),
            source=source,
            category=_clean(it.findtext("category", "") or ""),
        ))
    return out


def fetch_feed(category: str = "economy") -> list[FeedArticle]:
    """카테고리 피드를 받아 파싱해 반환."""
    url = FEEDS.get(category)
    if not url:
        raise ValueError(f"알 수 없는 피드 카테고리: {category!r} (가능: {list(FEEDS)})")
    return parse_feed(_get(url))
