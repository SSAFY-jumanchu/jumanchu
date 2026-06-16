"""
ai_review 조회 스크립트
사용법:
  python query_ai_review.py                  # 전체 목록 (50개씩)
  python query_ai_review.py --search 삼성     # 종목명/코드 검색
  python query_ai_review.py --market KOSPI   # 마켓 필터 (KOSPI/KOSDAQ/NASDAQ/S&P500)
  python query_ai_review.py --empty          # ai_review 없는 종목만
  python query_ai_review.py --count          # 통계만
"""

import os
import sys
import argparse
import psycopg2
from dotenv import load_dotenv

_dir = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(_dir, ".env"))
load_dotenv(dotenv_path=os.path.join(_dir, "..", ".env"), override=False)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "jumanchu"),
    "user": os.getenv("DB_USER", "jumanchu"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def show_stats(cur):
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(ai_review) FILTER (WHERE ai_review IS NOT NULL AND ai_review != '') AS filled,
            COUNT(*) FILTER (WHERE ai_review IS NULL OR ai_review = '') AS empty
        FROM stocks_stock
        WHERE is_active = TRUE
    """)
    total, filled, empty = cur.fetchone()
    print(f"전체: {total}  |  ai_review 있음: {filled}  |  없음: {empty}")

    cur.execute("""
        SELECT market, COUNT(*) AS total,
               COUNT(ai_review) FILTER (WHERE ai_review IS NOT NULL AND ai_review != '') AS filled
        FROM stocks_stock
        WHERE is_active = TRUE
        GROUP BY market ORDER BY market
    """)
    print("\n마켓별:")
    for market, total, filled in cur.fetchall():
        print(f"  {market:<12} 전체 {total:>5}  채움 {filled:>5}")


def show_rows(rows):
    if not rows:
        print("결과 없음")
        return
    for r in rows:
        print(f"[{r['code']}] {r['name']} ({r['market']})")
        if r.get("sector"):
            print(f"  업종: {r['sector']}")
        review = r.get("ai_review") or "(없음)"
        for line in review.split("\n"):
            print(f"  {line}")
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", "-s", help="종목명 또는 코드 검색")
    parser.add_argument("--market", "-m", help="마켓 필터 (KOSPI/KOSDAQ/NASDAQ/S&P500)")
    parser.add_argument("--empty", action="store_true", help="ai_review 없는 종목만")
    parser.add_argument("--count", action="store_true", help="통계만 출력")
    parser.add_argument("--limit", type=int, default=50, help="출력 개수 (기본 50)")
    args = parser.parse_args()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if args.count:
                show_stats(cur)
                return

            conditions = ["is_active = TRUE"]
            params = []

            if args.search:
                conditions.append("(name ILIKE %s OR code ILIKE %s)")
                params += [f"%{args.search}%", f"%{args.search}%"]
            if args.market:
                conditions.append("market = %s")
                params.append(args.market)
            if args.empty:
                conditions.append("(ai_review IS NULL OR ai_review = '')")

            where = " AND ".join(conditions)
            cur.execute(f"""
                SELECT code, name, market, sector, ai_review
                FROM stocks_stock
                WHERE {where}
                ORDER BY market, code
                LIMIT %s
            """, params + [args.limit])

            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]

            show_stats(cur)
            print(f"\n--- 조회 결과 ({len(rows)}개) ---\n")
            show_rows(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
