"""news_sector.extract_sectors 실제 RSS 검증 데모 (독립 실행)
============================================================
실제 구글뉴스/경제 피드에서 기사를 받아 섹터 추출 결과를 출력한다.
순수 함수(news_sector.py)가 진짜 뉴스에서 동작하는지 눈으로 확인하는 용도.

실행:  python 610jy/demo_news_sector.py
요구:  requests + stdlib (backend/venv에 있음). API 키 불필요.

주의:  아래 SAMPLE_STOCKS는 *데모용 하드코딩*이다. 실제 BE 연동 시에는
       Stock 테이블(code/name/sector)에서 로드한 StockRef 리스트를 넘긴다.
"""

from __future__ import annotations

import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

from news_sector import StockRef, extract_sectors

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0)"}

# 데모용 종목 사전 (실제론 Stock 테이블에서 로드) — name → sector 매핑이 핵심
SAMPLE_STOCKS: list[StockRef] = [
    StockRef("005930", "삼성전자", "반도체"),
    StockRef("000660", "SK하이닉스", "반도체"),
    StockRef("009150", "삼성전기", "전자부품"),
    StockRef("066570", "LG전자", "가전"),
    StockRef("373220", "LG에너지솔루션", "2차전지"),
    StockRef("006400", "삼성SDI", "2차전지"),
    StockRef("005380", "현대차", "자동차"),
    StockRef("000270", "기아", "자동차"),
    StockRef("035420", "NAVER", "인터넷"),
    StockRef("035720", "카카오", "인터넷"),
    StockRef("068270", "셀트리온", "바이오"),
    StockRef("207940", "삼성바이오로직스", "바이오"),
    StockRef("005490", "POSCO홀딩스", "철강"),
    StockRef("105560", "KB금융", "금융"),
]

# 섹터 추출을 보여줄 검색 키워드(종목명 위주)
TARGETS = ["삼성전자", "LG에너지솔루션", "현대차", "셀트리온"]


def google_news(keyword: str, limit: int = 8) -> list[dict]:
    q = quote(f"{keyword} 주식")
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError) as e:
        print(f"  ERROR: {e}")
        return []
    out = []
    for it in root.findall(".//item")[:limit]:
        title = (it.findtext("title") or "").rsplit(" - ", 1)[0].strip()
        out.append({"title": title})
    return out


if __name__ == "__main__":
    print(f"데모 종목 사전: {len(SAMPLE_STOCKS)}개 종목 / "
          f"{len({s.sector for s in SAMPLE_STOCKS})}개 섹터\n")

    for kw in TARGETS:
        print("=" * 72)
        print(f"[검색: {kw}]")
        print("=" * 72)
        articles = google_news(kw)
        if not articles:
            print("  (뉴스 없음)\n")
            continue

        for a in articles:
            tags = extract_sectors(a["title"], SAMPLE_STOCKS)
            label = (
                " · ".join(f"{t.sector}({t.score:.2f})" for t in tags)
                if tags else "—(섹터 미검출)"
            )
            print(f"  · {a['title']}")
            print(f"      → 섹터: {label}")
        print()
        time.sleep(1.0)

    print("[완료]")
