"""
구글뉴스 RSS → 종목 뉴스 수집 검증 (임시 테스트 스크립트)
=========================================================
목적: 정율 NEWS_API_SPEC §2-3의 구글뉴스 RSS 패턴이 실제로
      한국 종목 뉴스를 잘 주는지(헤드라인·시점) 확인.
      'AI 한 줄'은 이 출력 헤드라인을 보고 Claude가 생성(키 불필요).

요구: requests (backend/venv에 있음) + stdlib. OpenAI 키 불필요.
실행: backend/venv 파이썬으로
      python kis_test/news_rss_test.py
"""

from __future__ import annotations

import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

# Windows cp949 콘솔에서 한글/유니코드 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0)"}


def build_url(keyword: str, lang: str = "ko") -> str:
    """종목명/티커 → 구글뉴스 RSS 검색 URL (정율 §2-3 패턴)."""
    if lang == "ko":
        q = quote(f"{keyword} 주식")
        return f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    q = quote(f"{keyword} stock")
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def fetch_news(keyword: str, lang: str = "ko", limit: int = 5) -> list[dict]:
    url = build_url(keyword, lang)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERROR fetch: {e}")
        return []

    try:
        root = ET.fromstring(resp.content)  # bytes → 선언 인코딩 자동 처리
    except ET.ParseError as e:
        print(f"  ERROR parse: {e}")
        return []

    out: list[dict] = []
    for it in root.findall(".//item")[:limit]:
        src_el = it.find("source")
        out.append({
            "title": (it.findtext("title") or "").strip(),
            "source": (src_el.text.strip() if src_el is not None and src_el.text else ""),
            "pub": (it.findtext("pubDate") or "").strip(),
            "link": (it.findtext("link") or "").strip(),
        })
    return out


TARGETS = [
    ("삼성전자", "ko", "대형 - 뉴스 많음 예상"),
    ("로보스타", "ko", "중소형 - 뉴스 적을 케이스"),
    ("AAPL", "en", "해외 패턴"),
]


if __name__ == "__main__":
    for kw, lang, note in TARGETS:
        print("\n" + "=" * 72)
        print(f"[{kw}] ({lang}) — {note}")
        print(f"URL: {build_url(kw, lang)}")
        print("=" * 72)

        t0 = time.perf_counter()
        news = fetch_news(kw, lang, limit=5)
        dt = time.perf_counter() - t0

        if not news:
            print("  (뉴스 없음 / 실패)")
        else:
            print(f"  {len(news)}건 · 수집 {dt:.2f}s\n")
            for i, n in enumerate(news, 1):
                print(f"  {i}. {n['title']}")
                print(f"     · {n['source']}  |  {n['pub']}")
        time.sleep(1.0)  # 호출 간 간격(차단 회피)

    print("\n[완료]")
