"""
정율 메인 방식 검증: 경제 언론사 RSS 피드 + 종목 태깅
=====================================================
정율 NEWS_API_SPEC §2-1(국내 경제 피드) + §3-3(종목 태깅) 그대로 테스트.
구글뉴스 검색(보조)이 아니라, 경제 언론사 피드를 통째로 수집해
기사 제목/요약에서 관심종목명을 찾아 태깅한다.

목적: 경제 피드가 구글검색보다 '가십이 적고 등락 원인성 기사가 많은지' 비교.
요구: requests + stdlib. 키 불필요.
실행: python kis_test/news_feed_test.py
"""

from __future__ import annotations

import re
import sys
import time
import xml.etree.ElementTree as ET

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0)"}

# 정율 §2-1 국내 경제 피드 (네이버금융은 표준 RSS 아님 → 제외)
FEEDS = {
    "한국경제": "https://www.hankyung.com/feed/all-news",
    "매일경제": "https://www.mk.co.kr/rss/30000001/",
    "연합뉴스TV": "https://www.yonhapnewstv.co.kr/RSS/20.xml",
    "조선비즈": "https://biz.chosun.com/site/data/rss/rss.xml",
}

# 태깅용 관심종목 사전 (이름만; 실제론 STOCK 테이블에서 로드)
WATCH = [
    "삼성전자", "SK하이닉스", "삼성전기", "LG전자", "로보스타", "현대차",
    "NAVER", "네이버", "카카오", "기아", "셀트리온", "두산로보틱스",
    "삼성바이오로직스", "LG에너지솔루션", "포스코", "POSCO", "HD현대", "한화",
]

TAG = re.compile(r"<[^>]+>")


def strip_html(s: str) -> str:
    return TAG.sub(" ", s or "").strip()


def fetch_items(url: str) -> list[dict]:
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for it in root.findall(".//item"):
        items.append({
            "title": strip_html(it.findtext("title") or ""),
            "desc": strip_html(it.findtext("description") or ""),
            "pub": (it.findtext("pubDate") or "").strip(),
        })
    return items


def match_stocks(text: str) -> list[str]:
    return [name for name in WATCH if name in text]


if __name__ == "__main__":
    # stock -> [(title, feed, pub)]
    hits: dict[str, list[tuple[str, str, str]]] = {}
    total_scanned = 0

    for feed_name, url in FEEDS.items():
        try:
            t0 = time.perf_counter()
            items = fetch_items(url)
            dt = time.perf_counter() - t0
        except Exception as e:
            print(f"[{feed_name}] 실패: {e}")
            continue

        matched_cnt = 0
        for it in items:
            total_scanned += 1
            blob = it["title"] + " " + it["desc"]
            for name in match_stocks(blob):
                hits.setdefault(name, []).append((it["title"], feed_name, it["pub"]))
                matched_cnt += 1
        print(f"[{feed_name}] {len(items)}건 수집 ({dt:.2f}s) · 관심종목 언급 {matched_cnt}건")
        time.sleep(0.6)

    print(f"\n총 {total_scanned}건 스캔. 관심종목 태깅된 기사:\n")
    if not hits:
        print("  (관심종목 언급 기사 없음)")
    for name in sorted(hits, key=lambda n: -len(hits[n])):
        print(f"■ {name} — {len(hits[name])}건")
        for title, feed, pub in hits[name][:6]:
            print(f"   · {title}  [{feed} | {pub}]")
        print()
    print("[완료]")
