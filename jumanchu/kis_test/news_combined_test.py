"""
둘 합친 버전: 경제 피드(태깅) + 종목별 구글뉴스(출처 화이트리스트 + 날짜 필터)
==============================================================================
용도: '관련 기사' (인과 주장 X). 가십 제거 + 종목 커버리지 둘 다 확보.
- 구글뉴스 검색 → 경제/주요 매체 화이트리스트 + 최근 N일만 통과
- 경제 피드(한경·매경) → 종목명 태깅 매칭
- 합쳐서 제목 기준 중복 제거 → 최신순
요구: requests + stdlib. 키 불필요.
"""

from __future__ import annotations

import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0)"}
TAG = re.compile(r"<[^>]+>")
NOW = datetime.now(timezone.utc)
DAYS = 4

# 경제/주요 매체만 통과 (부분일치)
WHITELIST = [
    "한국경제", "한경", "매일경제", "매경", "서울경제", "이데일리", "머니투데이",
    "연합뉴스", "연합인포맥스", "인포맥스", "조선비즈", "파이낸셜뉴스", "헤럴드경제",
    "아시아경제", "뉴스핌", "비즈워치", "비즈니스워치", "전자신문", "디지털타임스",
    "디지털투데이", "조선일보", "중앙일보", "동아일보", "뉴스웨이", "한겨레", "더벨", "이코노미",
]

ECON_FEEDS = {
    "한국경제": "https://www.hankyung.com/feed/all-news",
    "매일경제": "https://www.mk.co.kr/rss/30000001/",
}


def strip_html(s: str) -> str:
    return TAG.sub(" ", s or "").strip()


def parse_dt(s: str):
    try:
        dt = parsedate_to_datetime(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def recent(dt) -> bool:
    return dt is None or (NOW - dt) <= timedelta(days=DAYS)


def whitelisted(src: str) -> bool:
    return any(w in src for w in WHITELIST)


def google_news(keyword: str, limit: int = 20) -> list[dict]:
    q = quote(f"{keyword} 주식")
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    out = []
    for it in root.findall(".//item")[:limit]:
        src_el = it.find("source")
        src = src_el.text.strip() if src_el is not None and src_el.text else ""
        title = strip_html(it.findtext("title") or "").rsplit(" - ", 1)[0]
        out.append({"title": title, "source": src, "dt": parse_dt(it.findtext("pubDate") or ""), "via": "구글"})
    return out


def feed_hits(keyword: str) -> list[dict]:
    out = []
    for name, url in ECON_FEEDS.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception:
            continue
        for it in root.findall(".//item"):
            title = strip_html(it.findtext("title") or "")
            desc = strip_html(it.findtext("description") or "")
            if keyword in (title + " " + desc):
                out.append({"title": title, "source": name, "dt": parse_dt(it.findtext("pubDate") or ""), "via": "피드"})
        time.sleep(0.4)
    return out


TARGETS = ["삼성전자", "로보스타"]


if __name__ == "__main__":
    print(f"기준 UTC {NOW:%Y-%m-%d %H:%M} · 최근 {DAYS}일 · 출처 화이트리스트 ON\n")
    for kw in TARGETS:
        g = google_news(kw)
        g_keep = [a for a in g if whitelisted(a["source"]) and recent(a["dt"])]
        f = feed_hits(kw)

        seen, merged = set(), []
        for a in g_keep + f:
            key = a["title"][:40]
            if key in seen:
                continue
            seen.add(key)
            merged.append(a)
        merged.sort(key=lambda a: a["dt"] or NOW, reverse=True)

        print("=" * 72)
        print(f"[{kw}] 구글 {len(g)}건 → 출처·날짜 통과 {len(g_keep)} | 피드 매칭 {len(f)} | 최종 {len(merged)}")
        print("=" * 72)
        for a in merged[:8]:
            d = a["dt"].strftime("%m-%d %H:%M") if a["dt"] else "?"
            print(f"  · [{a['via']}] {a['title']}  ({a['source']} | {d})")
        print()
    print("[완료]")
