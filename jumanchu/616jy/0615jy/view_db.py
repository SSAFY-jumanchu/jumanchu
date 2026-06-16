"""
DB 테이블 뷰어
사용법:
  python view_db.py                        # stocks_stock 표 (50행)
  python view_db.py --limit 100
  python view_db.py --search 삼성
  python view_db.py --market KOSPI
  python view_db.py --market NYSE
  python view_db.py --empty                # ai_review 없는 종목
  python view_db.py --tables              # DB 테이블 목록
  python view_db.py --table stocks_stock  # 특정 테이블 구조 확인
"""

import os
import sys
import argparse
import psycopg2
from tabulate import tabulate
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


def list_tables(cur):
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    rows = cur.fetchall()
    print(tabulate(rows, headers=["테이블명"], tablefmt="rounded_outline"))


def show_table_schema(cur, table):
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position
    """, (table,))
    rows = cur.fetchall()
    if not rows:
        print(f"테이블 '{table}' 없음")
        return
    print(f"\n[{table}] 컬럼 구조")
    print(tabulate(rows, headers=["컬럼", "타입", "최대길이", "NULL가능", "기본값"], tablefmt="rounded_outline"))


def show_stocks(cur, search=None, market=None, empty=False, limit=50):
    conditions = ["is_active = TRUE"]
    params = []

    if search:
        conditions.append("(name ILIKE %s OR code ILIKE %s)")
        params += [f"%{search}%", f"%{search}%"]
    if market:
        conditions.append("market = %s")
        params.append(market)
    if empty:
        conditions.append("(ai_review IS NULL OR ai_review = '')")

    where = " AND ".join(conditions)
    cur.execute(f"""
        SELECT code, name, market, sector,
               LEFT(ai_review, 60) AS ai_review_preview
        FROM stocks_stock
        WHERE {where}
        ORDER BY market, code
        LIMIT %s
    """, params + [limit])

    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()

    # 통계
    cur.execute("""
        SELECT COUNT(*),
               COUNT(ai_review) FILTER (WHERE ai_review IS NOT NULL AND ai_review != ''),
               COUNT(*) FILTER (WHERE ai_review IS NULL OR ai_review = '')
        FROM stocks_stock WHERE is_active = TRUE
    """)
    total, filled, empty_cnt = cur.fetchone()
    print(f"전체: {total}  |  ai_review 있음: {filled}  |  없음: {empty_cnt}\n")

    headers = ["코드", "종목명", "마켓", "업종", "ai_review (60자)"]
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline", maxcolwidths=[8, 16, 8, 14, 62]))
    print(f"\n{len(rows)}행 표시 (limit={limit})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", "-s", help="종목명/코드 검색")
    parser.add_argument("--market", "-m", help="마켓 필터 (KOSPI/KOSDAQ/NYSE/NASDAQ)")
    parser.add_argument("--empty", action="store_true", help="ai_review 없는 종목만")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--tables", action="store_true", help="DB 테이블 목록")
    parser.add_argument("--table", help="특정 테이블 컬럼 구조 확인")
    args = parser.parse_args()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if args.tables:
                list_tables(cur)
            elif args.table:
                show_table_schema(cur, args.table)
            else:
                show_stocks(cur, search=args.search, market=args.market,
                            empty=args.empty, limit=args.limit)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
