"""종목별 뉴스 수집 — US-06 종목 상세 "관련 뉴스 탭" (Algo 담당: 정율)
========================================================================
방향: **종목 → 뉴스**. 사용자가 종목을 클릭하면 그 종목 상세 페이지의 뉴스 탭에
      들어갈 기사 리스트를 만든다. (오늘 만든 news_sector.py는 반대 방향 US-05용)

설계 결정(2026-06-10):
  - 순수 로직(검색어 생성 · 출처 화이트리스트 · 최근성 · 중복제거 · 관련도 정렬)과
    네트워크 fetch를 **분리**한다. fetch는 `fetcher`로 주입 → BE(재민)가 실제 외부
    API 연동/캐싱을 담당하고(CLAUDE.md: 외부 API 연동=BE), Algo는 로직만 책임.
  - 검증된 방식(kis_test/news_combined_test.py)을 함수로 정리: 구글뉴스 검색
    (종목명) + 경제 매체 화이트리스트 + 최근 N일 + 제목 기준 중복제거 → 최신순.

BE ↔ Algo 인터페이스:
    items = fetch_stock_news(stock, days=4, limit=10)   # 기본 fetcher=구글뉴스 RSS
    payload = [it.to_dict() for it in items]            # 종목 상세 뉴스 탭 응답
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Protocol
from urllib.parse import quote


# --------------------------------------------------------------------------- #
# 입출력 타입 (BE↔Algo 계약)
# --------------------------------------------------------------------------- #
class StockLike(Protocol):
    """BE가 넘기는 Stock 행의 최소 인터페이스 (Django 모델/네임드튜플 무관)."""
    code: str
    name: str
    market: str          # 'KOSPI'/'KOSDAQ'/'NASDAQ' 등 — 국내/해외 판별용
    sector: str          # Stock.sector — 테마 뉴스용(비어있으면 테마 생략)


@dataclass(frozen=True)
class StockNewsItem:
    """종목 상세 뉴스 탭에 들어갈 기사 1건."""
    title: str
    source: str
    url: str
    published_at: datetime | None
    summary: str = ""   # 기사 요약(있을 때만). Google News는 본문 미제공 → 빈 값

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
        }


# --------------------------------------------------------------------------- #
# 순수 로직 (네트워크 무관 — Algo 책임 영역)
# --------------------------------------------------------------------------- #
# 경제/주요 매체만 통과(부분일치) — 가십·블로그 제거
SOURCE_WHITELIST: tuple[str, ...] = (
    "한국경제", "한경", "매일경제", "매경", "서울경제", "이데일리", "머니투데이",
    "연합뉴스", "연합인포맥스", "인포맥스", "조선비즈", "파이낸셜뉴스", "헤럴드경제",
    "아시아경제", "뉴스핌", "비즈워치", "비즈니스워치", "전자신문", "디지털타임스",
    "조선일보", "중앙일보", "동아일보", "한겨레", "더벨", "이코노미",
    # 해외(영문 종목용)
    "Reuters", "Bloomberg", "CNBC", "Yahoo", "MarketWatch", "Barron",
)

_DOMESTIC_MARKETS = {"KOSPI", "KOSDAQ", "KONEX"}
_TAG = re.compile(r"<[^>]+>")


def is_domestic(stock: StockLike) -> bool:
    return stock.market in _DOMESTIC_MARKETS


def _google_news_url(query: str, *, domestic: bool) -> str:
    """검색어 → 구글뉴스 RSS URL. 로케일로 국장(ko)/미장(en) 전환."""
    q = quote(query)
    if domestic:
        return f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def build_news_query(stock: StockLike) -> str:
    """종목 → 그 종목 직접 뉴스 검색 URL. 국내는 종목명, 해외는 티커 기준."""
    if is_domestic(stock):
        return _google_news_url(f"{stock.name} 주식", domestic=True)
    return _google_news_url(f"{stock.code} stock", domestic=False)


def build_theme_query(sector: str, *, domestic: bool) -> str:
    """섹터/테마 → 그 테마 관련주 뉴스 검색 URL.
    국내 Stock.sector는 한글(예:'반도체'), 해외는 영문(예:'Semiconductors')이라
    로케일과 자연히 맞는다."""
    if domestic:
        return _google_news_url(f"{sector} 관련주", domestic=True)
    return _google_news_url(f"{sector} sector stocks", domestic=False)


def is_whitelisted(source: str, whitelist: tuple[str, ...] = SOURCE_WHITELIST) -> bool:
    return any(w in source for w in whitelist)


def is_recent(dt: datetime | None, days: int, *, now: datetime | None = None) -> bool:
    """발행 시각이 최근 N일 이내인지. dt 미상이면 보수적으로 통과시킨다."""
    if dt is None:
        return True
    now = now or datetime.now(timezone.utc)
    return (now - dt) <= timedelta(days=days)


def _strip_html(s: str) -> str:
    return _TAG.sub(" ", s or "").strip()


def _parse_dt(s: str) -> datetime | None:
    try:
        dt = parsedate_to_datetime(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def dedup_by_title(items: list[StockNewsItem], head: int = 40) -> list[StockNewsItem]:
    """제목 앞 head글자 기준 중복 제거(같은 기사 다른 매체 재배포 컷)."""
    seen: set[str] = set()
    out: list[StockNewsItem] = []
    for it in items:
        key = it.title[:head]
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def rank_news(items: list[StockNewsItem]) -> list[StockNewsItem]:
    """최신순 정렬(발행시각 미상은 뒤로)."""
    return sorted(
        items,
        key=lambda it: it.published_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )


# --------------------------------------------------------------------------- #
# 네트워크 fetch (기본 구현 — BE가 교체/캐싱 래핑 가능)
# --------------------------------------------------------------------------- #
Fetcher = Callable[[str], bytes]


def _default_fetcher(url: str) -> bytes:
    """기본 RSS fetch. BE는 캐싱/타임아웃 정책에 맞춰 주입 교체 가능."""
    import requests  # 지연 import — 순수 로직만 쓸 땐 requests 불필요

    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0)"},
        timeout=12,
    )
    resp.raise_for_status()
    return resp.content


def _parse_rss(raw: bytes) -> list[StockNewsItem]:
    root = ET.fromstring(raw)
    items: list[StockNewsItem] = []
    for it in root.findall(".//item"):
        src_el = it.find("source")
        source = src_el.text.strip() if src_el is not None and src_el.text else ""
        # 구글뉴스 제목은 "제목 - 매체" 꼴 → 매체명 분리
        raw_title = _strip_html(it.findtext("title") or "")
        title = raw_title.rsplit(" - ", 1)[0]
        items.append(StockNewsItem(
            title=title,
            source=source,
            url=(it.findtext("link") or "").strip(),
            published_at=_parse_dt(it.findtext("pubDate") or ""),
        ))
    return items


# --------------------------------------------------------------------------- #
# 공개 진입점
# --------------------------------------------------------------------------- #
def _collect(
    url: str,
    *,
    days: int,
    limit: int,
    whitelist: tuple[str, ...],
    fetcher: Fetcher,
    exclude_titles: set[str] = frozenset(),
) -> list[StockNewsItem]:
    """공통 수집 파이프라인: fetch → 파싱 → 최근성+화이트리스트 → 중복제거 → 정렬."""
    try:
        raw = fetcher(url)
    except Exception:  # 외부 API 실패는 빈 결과로(상세 페이지 다른 탭은 살아야 함)
        return []

    items = _parse_rss(raw)
    recent = [it for it in items if is_recent(it.published_at, days)]
    # 품질 출처(화이트리스트) 우선. 단 0건이면 탭이 비므로 최근성만으로 fallback.
    quality = [it for it in recent if is_whitelisted(it.source, whitelist)]
    ranked = rank_news(dedup_by_title(quality if quality else recent))
    if exclude_titles:
        ranked = [it for it in ranked if it.title[:40] not in exclude_titles]
    return ranked[:limit]


def fetch_stock_news(
    stock: StockLike,
    *,
    days: int = 4,
    limit: int = 10,
    whitelist: tuple[str, ...] = SOURCE_WHITELIST,
    fetcher: Fetcher = _default_fetcher,
) -> list[StockNewsItem]:
    """종목 상세 '뉴스 탭'용 — 그 종목 직접 기사 리스트.

    파이프라인: 검색 URL 생성 → fetch → 파싱 → 화이트리스트+최근성 → 중복제거 →
                최신순 → 상위 limit. 실패 시 빈 리스트.
    """
    return _collect(
        build_news_query(stock),
        days=days, limit=limit, whitelist=whitelist, fetcher=fetcher,
    )


def fetch_theme_news(
    sector: str,
    *,
    domestic: bool,
    days: int = 7,
    limit: int = 10,
    whitelist: tuple[str, ...] = SOURCE_WHITELIST,
    fetcher: Fetcher = _default_fetcher,
    exclude_titles: set[str] = frozenset(),
) -> list[StockNewsItem]:
    """종목 상세 '테마 뉴스' — 같은 섹터/테마 관련주 기사.

    Args:
        sector: Stock.sector (예: '반도체' / 'Semiconductors'). 비면 빈 리스트.
        domestic: 국내장 여부(로케일 ko/en 결정).
        exclude_titles: 직접 뉴스와 중복 제거용(제목 앞 40자 집합).
    """
    if not sector.strip():
        return []
    return _collect(
        build_theme_query(sector, domestic=domestic),
        days=days, limit=limit, whitelist=whitelist, fetcher=fetcher,
        exclude_titles=exclude_titles,
    )


def fetch_stock_detail_news(
    stock: StockLike,
    *,
    days: int = 7,
    limit: int = 8,
    fetcher: Fetcher = _default_fetcher,
) -> dict[str, list[StockNewsItem]]:
    """US-06 종목 상세 진입점 — 그 종목 뉴스 + 테마(섹터) 뉴스 한 번에.

    Returns:
        {"stock_news": [...], "theme_news": [...]}.
        테마는 직접 뉴스와 제목 중복을 제거해 두 탭이 안 겹치게 한다.
        sector가 비어있으면 theme_news는 빈 리스트.
    """
    direct = fetch_stock_news(stock, days=days, limit=limit, fetcher=fetcher)
    sector = getattr(stock, "sector", "") or ""
    theme = fetch_theme_news(
        sector,
        domestic=is_domestic(stock),
        days=days, limit=limit, fetcher=fetcher,
        exclude_titles={it.title[:40] for it in direct},
    )
    return {"stock_news": direct, "theme_news": theme}
