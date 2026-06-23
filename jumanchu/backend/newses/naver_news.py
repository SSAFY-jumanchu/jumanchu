"""네이버 검색 API 기반 국장 종목 뉴스 + 본문 전체 추출.

원본: 정율(Algo) `610jy/naver_news.py` — 검증된 순수 stdlib 모듈을 newses 앱으로
들여오면서 자격증명 로딩만 백엔드 환경(`backend/.env`)에 맞게 조정했다.

왜 네이버:
  - 검색 기반 → 국장 전 종목 커버(고정 피드 한계 없음).
  - `link`이 news.naver.com(네이버 호스팅)일 때 본문 DOM(#dic_area)이 일관 →
    전체 본문 추출이 깔끔.

자격증명: 환경변수(NAVER_CLIENT_ID/SECRET 또는 CLIENT_ID/SECRET) 우선,
    없으면 backend/.env 에서 직접 로드 → Django/단독 스크립트 양쪽 모두 동작.

저작권 주의: 본문 '저장/재배포'는 피하고, 추천 신호 추출·요약 등 가공 용도로만.
    영구 저장은 링크+요약 위주 권장.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

NAVER_NEWS_ENDPOINT = "https://openapi.naver.com/v1/search/news.json"
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"   # backend/.env
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t 　]+")
_NL = re.compile(r"\n{3,}")
MAX_BODY_CHARS = 2000   # 본문 최대 길이(초과 시 잘라서 반환)


# --------------------------------------------------------------------------- #
# 자격증명 로드
# --------------------------------------------------------------------------- #
def _read_env_file(path: Path) -> dict[str, str]:
    kv: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        kv[k.strip()] = v.strip().strip('"').strip("'")
    return kv


def load_credentials() -> tuple[str, str]:
    """네이버 검색 API Client ID/Secret 로드.

    우선순위: 환경변수(NAVER_CLIENT_ID/SECRET → CLIENT_ID/SECRET) → backend/.env.
    Django 실행 시 settings 가 backend/.env 를 os.environ 으로 올리고, 단독 스크립트
    실행 시엔 이 함수가 backend/.env 를 직접 읽어 양쪽 모두 동작한다.
    """
    cid = os.environ.get("NAVER_CLIENT_ID") or os.environ.get("CLIENT_ID")
    sec = os.environ.get("NAVER_CLIENT_SECRET") or os.environ.get("CLIENT_SECRET")
    if not (cid and sec) and _ENV_FILE.exists():
        kv = _read_env_file(_ENV_FILE)
        cid = cid or kv.get("NAVER_CLIENT_ID") or kv.get("CLIENT_ID")
        sec = sec or kv.get("NAVER_CLIENT_SECRET") or kv.get("CLIENT_SECRET")
    if not (cid and sec):
        raise RuntimeError(
            "네이버 검색 API 키 없음. backend/.env 에 CLIENT_ID/CLIENT_SECRET 를 "
            "넣거나 환경변수 NAVER_CLIENT_ID/NAVER_CLIENT_SECRET 를 설정하세요."
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
    source: str = ""         # 언론사명 (originallink 도메인에서 역산)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.origin_link or self.naver_link,
            "source": self.source,
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


# 도메인 → 언론사명. 네이버 검색 API는 언론사명을 안 주므로 originallink 로 역산.
# 미등록 도메인은 호스트 그대로 노출(폴백). 잘못된 이름이 폴백보다 나쁘니 확신 매체만 등재.
_PRESS_BY_DOMAIN = {
    # 통신/방송
    "yna.co.kr": "연합뉴스", "yonhapnewstv.co.kr": "연합뉴스TV", "newsis.com": "뉴시스",
    "news1.kr": "뉴스1", "newspim.com": "뉴스핌", "nocutnews.co.kr": "노컷뉴스",
    "mbn.co.kr": "MBN", "ytn.co.kr": "YTN", "sbs.co.kr": "SBS", "kbs.co.kr": "KBS",
    "imbc.com": "MBC", "mtn.co.kr": "머니투데이방송",
    # 경제/증권 일간
    "hankyung.com": "한국경제", "wowtv.co.kr": "한국경제TV", "mk.co.kr": "매일경제",
    "mt.co.kr": "머니투데이", "moneys.co.kr": "머니S", "sedaily.com": "서울경제",
    "fnnews.com": "파이낸셜뉴스", "asiae.co.kr": "아시아경제", "heraldcorp.com": "헤럴드경제",
    "edaily.co.kr": "이데일리", "etoday.co.kr": "이투데이", "ajunews.com": "아주경제",
    "g-enews.com": "글로벌이코노믹", "viva100.com": "브릿지경제", "economist.co.kr": "이코노미스트",
    # 경제 전문/주식
    "bizwatch.co.kr": "비즈워치", "thebell.co.kr": "더벨", "businesspost.co.kr": "비즈니스포스트",
    "paxnetnews.com": "팍스넷뉴스", "infostockdaily.co.kr": "인포스탁데일리",
    "dealsite.co.kr": "딜사이트", "bizhankook.com": "비즈한국", "theguru.co.kr": "더구루",
    "greened.kr": "녹색경제신문", "webeconomy.co.kr": "웹이코노미", "ftoday.co.kr": "금융투데이",
    # IT/테크
    "etnews.com": "전자신문", "ddaily.co.kr": "디지털데일리", "dt.co.kr": "디지털타임스",
    "zdnet.co.kr": "ZDNet코리아", "bloter.net": "블로터", "techm.kr": "테크M",
    "it.chosun.com": "IT조선",
    # 가상자산
    "tokenpost.kr": "토큰포스트", "blockmedia.co.kr": "블록미디어",
    # 종합 일간
    "biz.chosun.com": "조선비즈", "chosun.com": "조선일보", "joongang.co.kr": "중앙일보",
    "donga.com": "동아일보", "hani.co.kr": "한겨레", "khan.co.kr": "경향신문",
    "kmib.co.kr": "국민일보", "seoul.co.kr": "서울신문", "munhwa.com": "문화일보",
    "hankookilbo.com": "한국일보", "segye.com": "세계일보", "ohmynews.com": "오마이뉴스",
    "dailian.co.kr": "데일리안", "pressian.com": "프레시안", "tf.co.kr": "더팩트",
    "wikitree.co.kr": "위키트리", "insight.co.kr": "인사이트",
    # 네이버 호스팅(원문 도메인 없을 때 폴백)
    "news.naver.com": "네이버뉴스",
    # 해외
    "bloomberg.com": "Bloomberg", "reuters.com": "Reuters",
}


def _press_from_url(url: str) -> str:
    """기사 URL 도메인 → 언론사명. 미등록이면 호스트(www. 제거)를 그대로 반환."""
    if not url:
        return ""
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host in _PRESS_BY_DOMAIN:
        return _PRESS_BY_DOMAIN[host]
    for domain, name in _PRESS_BY_DOMAIN.items():
        if host.endswith("." + domain):
            return name
    return host


def build_query(stock_name: str) -> str:
    """종목명 → 네이버 뉴스 검색어. '주식'을 붙여 증시 맥락으로 좁힘."""
    return f"{stock_name} 주식"


def is_naver_hosted(url: str) -> bool:
    return "news.naver.com" in url


def extract_body(html: str) -> str:
    """news.naver.com 본문 컨테이너(#dic_area / #newsct_article)에서 본문 추출.
    네이버 호스팅 기사 DOM은 일관적이라 stdlib 정규식으로 충분."""
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
                return body[:MAX_BODY_CHARS]
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
    cid, sec = load_credentials()
    url = f"{NAVER_NEWS_ENDPOINT}?query={quote(query)}&display={display}&sort={sort}"
    raw = _get(url, {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec})
    data = json.loads(raw)
    out: list[NaverArticle] = []
    for it in data.get("items", []):
        origin = it.get("originallink", "").strip()
        link = it.get("link", "").strip()
        out.append(NaverArticle(
            title=_clean(it.get("title", "")),
            naver_link=link,
            origin_link=origin,
            published_at=_parse_dt(it.get("pubDate", "")),
            summary=_clean(it.get("description", "")),
            source=_press_from_url(origin or link),
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
            a.title, a.naver_link, a.origin_link, a.published_at, a.summary, body, a.source
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
