"""
주식 AI 리뷰 생성 스크립트
- stocks_stock 테이블에서 종목 목록 읽기
- GMS(gpt-4o-mini)로 2줄 분석 요약 생성
- ai_review 컬럼에 UPDATE
"""

import os
import time
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

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

GMS_API_KEY = os.getenv("GMS_API_KEY", "")
MODEL = "gpt-4o-mini"
RATE_LIMIT_SEC = 0.5


def get_client() -> OpenAI:
    if not GMS_API_KEY:
        raise ValueError(".env에 GMS_API_KEY가 없습니다.")
    return OpenAI(api_key=GMS_API_KEY, base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1/")


def ensure_ai_review_column(cur):
    cur.execute("""
        ALTER TABLE stocks_stock
        ADD COLUMN IF NOT EXISTS ai_review VARCHAR(300);
    """)


def fetch_stocks(cur) -> list[dict]:
    cur.execute("""
        SELECT id, code, name, market, sector, industry
        FROM stocks_stock
        WHERE is_active = TRUE
          AND (ai_review IS NULL OR ai_review = '')
        ORDER BY market, code
    """)
    cols = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def build_prompt(stock: dict) -> str:
    parts = [f"종목명: {stock['name']} ({stock['code']}, {stock['market']})"]
    if stock.get("sector"):
        parts.append(f"업종: {stock['sector']}")
    if stock.get("industry"):
        parts.append(f"산업: {stock['industry']}")
    info = " / ".join(parts)
    return (
        f"다음 주식 종목에 대해 한국어 2줄로 작성해줘.\n"
        f"1줄: 이 회사가 하는 핵심 사업과 주력 제품·서비스\n"
        f"2줄: 이 회사의 사업 구조나 특징 (알고 있는 사실만, 모르면 업종 기반으로 일반적 특징 서술)\n"
        f"조건: 확인되지 않은 수치·순위·글로벌 진출 여부 등 검증 불가한 내용 절대 금지, 각 줄 40자 이내, 번호 없이 줄바꿈 구분, 2줄만 출력.\n\n{info}"
    )


def generate_review(client: OpenAI, stock: dict) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": build_prompt(stock)}],
        max_tokens=150,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def update_review(cur, stock_id: int, review: str):
    cur.execute(
        "UPDATE stocks_stock SET ai_review = %s WHERE id = %s",
        (review, stock_id),
    )


def main():
    client = get_client()
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn:
            with conn.cursor() as cur:
                ensure_ai_review_column(cur)
                print("ai_review 컬럼 확인 완료")

        with conn.cursor() as cur:
            stocks = fetch_stocks(cur)

        print(f"리뷰 생성 대상: {len(stocks)}개 종목\n")

        for i, stock in enumerate(stocks, 1):
            try:
                review = generate_review(client, stock)
                with conn:
                    with conn.cursor() as cur:
                        update_review(cur, stock["id"], review)
                print(f"[{i}/{len(stocks)}] {stock['code']} {stock['name']}\n  → {review}\n")
            except Exception as e:
                print(f"[{i}/{len(stocks)}] {stock['code']} {stock['name']} 실패: {e}")

            if i < len(stocks):
                time.sleep(RATE_LIMIT_SEC)

        print("완료!")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
