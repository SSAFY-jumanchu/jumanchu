"""GMS(SSAFY) LLM 콜러블 — 0615jy 패턴과 동일.
=================================================
OpenAI SDK를 그대로 쓰되 base_url을 GMS 프록시로, 키는 `GMS_API_KEY`로 사용한다.
`longterm_report.build_longterm_report(..., llm=...)`에 넣을 `llm(prompt)->str`를 만든다.

요구사항: pip install openai python-dotenv
환경변수: GMS_API_KEY  (.env 또는 Django settings/env)

참고: 0615jy/test_gms.py·label_stocks.py 와 base_url·키 동일.
"""

from __future__ import annotations

import os
from typing import Callable

from openai import OpenAI

GMS_BASE_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/"
# GMS가 노출하는 4o 모델 id. 0615jy는 "gpt-4o-mini" 사용 — "4o pro" 실제 id는 확인 후 조정.
DEFAULT_MODEL = "gpt-4o"


def make_gms_caller(
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.4,
    max_tokens: int = 900,
    force_json: bool = False,
) -> Callable[[str], str]:
    """GMS GPT-4o용 `llm(prompt)->str` 콜러블 생성.

    BE 사용:
        from gms_client import make_gms_caller
        from longterm_report import build_longterm_report
        llm = make_gms_caller(api_key=settings.GMS_API_KEY)   # 또는 .env GMS_API_KEY
        report = build_longterm_report(meta, fin, grw, scores, profile, llm=llm)

    force_json=True 면 response_format=json_object 강제(파싱 안정성↑). gpt-4o 계열 지원.
    """
    key = api_key or os.getenv("GMS_API_KEY")
    if not key:
        raise ValueError("GMS_API_KEY가 없습니다 (.env 또는 settings).")
    client = OpenAI(api_key=key, base_url=GMS_BASE_URL)

    def _call(prompt: str) -> str:
        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if force_json:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()

    return _call


if __name__ == "__main__":
    # 키가 있으면 실제 1콜 (4o pro 응답 확인용). 없으면 안내만.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    if not os.getenv("GMS_API_KEY"):
        print("GMS_API_KEY 없음 — .env에 설정 후 다시 실행하세요.")
    else:
        from longterm_report import (
            FinancialMetrics, GrowthMetrics, LongTermScores, StockMeta, UserProfile,
            build_longterm_report,
        )
        import json

        llm = make_gms_caller()
        report = build_longterm_report(
            StockMeta("000660", "SK하이닉스", "KOSPI", "반도체", "KRW"),
            FinancialMetrics(debt_ratio=22.4, current_ratio=198.3,
                             operating_margin=32.1, net_margin=24.5, roe=26.78),
            GrowthMetrics(revenue_yoy=48.2, operating_profit_yoy=120.5, net_profit_yoy=90.1),
            LongTermScores(financial=78, growth=92, total=86, userfit=87),
            UserProfile("공격형", 12, ["반도체", "전기전자"], 38.4),
            llm=llm,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
