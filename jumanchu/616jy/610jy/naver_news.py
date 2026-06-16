"""네이버 검색 API 기반 국장 종목 뉴스 + 본문 전체 추출 (Algo: 정율)
=====================================================================
국장(KR) 종목 뉴스를 네이버 검색 API로 받고, news.naver.com 본문 DOM에서
기사 **전체 본문**을 추출한다. (미장은 stock_news.py의 Yahoo 경로 사용)

왜 네이버:
  - 검색 기반 → 국장 전 종목 커버(고정 피드 한계 없음).
  - `link`이 news.naver.com(네이버 호스팅)일 때 본문 DOM(#dic_area)이 일관 →
    전체 본문 추출이 깔끔. Google News처럼 인코딩 URL 디코딩 불필요.

키: 무료 발급(developers.naver.com, 검색 API). 환경변수 NAVER_CLIENT_ID/SECRET
    또는 610jy/naver_keys.local 파일에서 로드(둘 다 git 커밋 금지).

저작권 주의(NEWS_API_SPEC §7-1): 본문 '저장/재배포'는 피하고, 추천 신호 추출·
요약 등 가공 용도로만. 영구 저장은 링크+요약 위주 권장.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

NAVER_NEWS_ENDPOINT = "https://openapi.naver.com/v1/search/news.json"
_KEYS_FILE = Path(__file__).with_name("naver_keys.local")
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t ]+")
_NL = re.compile(r"\n{3,}")


# --------------------------------------------------------------------------- #
# 자격증명 로드
# --------------------------------------------------------------------------- #
def load_credentials() -> tuple[str, str]:
    """환경변수 우선, 없으면 naver_keys.local에서 Client ID/Secret 로드."""
    cid = os.environ.get("NAVER_CLIENT_ID")
    sec = os.environ.get("NAVER_CLIENT_SECRET")
    if cid and sec:
        return cid, sec
    if _KEYS_FILE.exists():
        kv = {}
        for line in _KEYS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                kv[k.strip()] = v.strip().strip('"')
        cid = cid or kv.get("NAVER_CLIENT_ID")
        sec = sec or kv.get("NAVER_CLIENT_SECRET")
    if not (cid and sec):
        raise RuntimeError(
            "네이버 키 없음. 환경변수 NAVER_CLIENT_ID/SECRET 또는 "
            f"{_KEYS_FILE.name} 파일을 설정하세요."
        )
    return cid, sec


# --------------------------------------------------------------------------- #
# 타입
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NaverArticle:
    title: str
    naver_link: str          # news.naver.com 링크(본문 추출 대상). 없으면 원문과 동일
    origin_link: str         # 언론사 원문 URL
    published_at: datetime | None
    summary: str             # 검색 API description(요약 스니펫)
    body: str = ""           # 본문 전체(추출 성공 시)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.origin_link or self.naver_link,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "body": self.body,
        }


# --------------------------------------------------------------------------- #
# 순수 헬퍼
# --------------------------------------------------------------------------- #
def _clean(text: str) -> str:
    return _WS.sub(" ", unescape(_TAG.sub("", text or ""))).strip()


def _parse_dt(s: str) -> datetime | None:
    try:
        dt = parsedate_to_datetime(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def build_query(stock_name: str) -> str:
    """종목명 → 네이버 뉴스 검색어. '주식'을 붙여 증시 맥락으로 좁힘."""
    return f"{stock_name} 주식"


def is_naver_hosted(url: str) -> bool:
    return "news.naver.com" in url


def extract_body(html: str) -> str:
    """news.naver.com 본문 컨테이너(#dic_area / #newsct_article)에서 본문 추출.
    네이버 호스팅 기사 DOM은 일관적이라 stdlib 정규식으로 충분."""
    # 본문 영역 후보(데스크톱/모바일/연예/스포츠 일부 차이 흡수)
    for pat in (
        r'id="dic_area"[^>]*>(.*?)</article>',
        r'id="dic_area"[^>]*>(.*?)</div>',
        r'id="newsct_article"[^>]*>(.*?)</article>',
        r'class="news_end"[^>]*>(.*?)</div>',
    ):
        m = re.search(pat, html, re.S)
        if m:
            raw = m.group(1)
            raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
            raw = re.sub(r"<span class=\"end_photo_org\">.*?</span>", " ", raw, flags=re.S)
            raw = raw.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
            body = _clean(raw)
            body = _NL.sub("\n\n", body)
            if len(body) > 40:        # 너무 짧으면 잘못 잡은 것
                return body
    return ""


# --------------------------------------------------------------------------- #
# 네트워크
# --------------------------------------------------------------------------- #
def _get(url: str, headers: dict[str, str], timeout: int = 12) -> bytes:
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def search_news(
    query: str,
    *,
    display: int = 10,
    sort: str = "date",          # 'date'(최신) | 'sim'(정확도)
) -> list[NaverArticle]:
    """네이버 뉴스 검색. 본문(body)은 아직 비어있음 → enrich_bodies로 채움."""
    import json

    cid, sec = load_credentials()
    url = f"{NAVER_NEWS_ENDPOINT}?query={quote(query)}&display={display}&sort={sort}"
    raw = _get(url, {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec})
    data = json.loads(raw)
    out: list[NaverArticle] = []
    for it in data.get("items", []):
        out.append(NaverArticle(
            title=_clean(it.get("title", "")),
            naver_link=it.get("link", "").strip(),
            origin_link=it.get("originallink", "").strip(),
            published_at=_parse_dt(it.get("pubDate", "")),
            summary=_clean(it.get("description", "")),
        ))
    return out


def enrich_bodies(
    articles: list[NaverArticle],
    *,
    limit: int | None = None,
    ua: str = "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0)",
) -> list[NaverArticle]:
    """네이버 호스팅 기사에 한해 본문 전체를 추출해 body 채운 새 리스트 반환.
    (원문 직접 호스팅은 DOM이 제각각이라 summary로 대체)"""
    enriched: list[NaverArticle] = []
    done = 0
    for a in articles:
        body = ""
        if (limit is None or done < limit) and is_naver_hosted(a.naver_link):
            try:
                html = _get(a.naver_link, {"User-Agent": ua}).decode("utf-8", "replace")
                body = extract_body(html)
                done += 1
            except Exception:
                body = ""
        enriched.append(NaverArticle(
            a.title, a.naver_link, a.origin_link, a.published_at, a.summary, body
        ))
    return enriched


def fetch_stock_articles(
    stock_name: str,
    *,
    display: int = 30,
    sort: str = "date",
    limit: int = 8,
    body_limit: int = 8,
    hosted_only: bool = True,
) -> list[NaverArticle]:
    """국장 종목 → 검색 + 본문 전체 추출까지 한 번에.

    네이버 호스팅(news.naver.com) 기사만 본문 DOM이 일관되므로, 본문 전체를 원하면
    hosted_only=True로 군소 매체(원문 직접 호스팅)를 걸러낸다. display를 넉넉히 받아
    호스팅 기사 위주로 상위 limit개를 본문까지 채워 반환.
    """
    found = search_news(build_query(stock_name), display=display, sort=sort)
    if hosted_only:
        found = [a for a in found if is_naver_hosted(a.naver_link)]
    found = found[:limit]
    return enrich_bodies(found, limit=body_limit)
