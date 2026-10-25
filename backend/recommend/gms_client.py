"""GMS(SSAFY) LLM 콜러블 — 장투 리포트용.

※ 정율(Algo) 616jy/gms_client.py를 BE로 포팅. OpenAI SDK를 그대로 쓰되 base_url을 GMS
   프록시로, 키는 settings.GMS_API_KEY(.env의 GMS_API_KEY)로 사용한다.
   `longterm_report.build_longterm_report(..., llm=...)`에 넣을 `llm(prompt)->str`를 만든다.

요구사항: openai>=1.55 (requirements.txt) · .env에 GMS_API_KEY
"""
from __future__ import annotations

import os
from typing import Callable

GMS_BASE_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/"
DEFAULT_MODEL = "gpt-4o"


def make_gms_caller(
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.4,
    max_tokens: int = 900,
    force_json: bool = True,
) -> Callable[[str], str]:
    """GMS GPT-4o용 `llm(prompt)->str` 콜러블 생성.

    force_json=True 면 response_format=json_object 강제(파싱 안정성↑). gpt-4o 계열 지원.
    """
    key = api_key or os.getenv("GMS_API_KEY")
    if not key:
        raise ValueError("GMS_API_KEY가 없습니다 (.env 또는 settings).")
    from openai import OpenAI  # 지연 import: 리포트 안 쓰는 경로는 openai 미설치여도 동작

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
