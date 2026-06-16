from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(".env")
client = OpenAI(api_key=os.getenv("GMS_API_KEY"), base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1/")

prompt = (
    "다음 주식 종목에 대해 한국어 2줄로 작성해줘.\n"
    "1줄: 이 회사가 하는 핵심 사업과 주력 제품·서비스\n"
    "2줄: 이 회사의 사업 구조나 특징 (알고 있는 사실만, 모르면 업종 기반으로 일반적 특징 서술)\n"
    "조건: 확인되지 않은 수치·순위·글로벌 진출 여부 등 검증 불가한 내용 절대 금지, 각 줄 40자 이내, 번호 없이 줄바꿈 구분, 2줄만 출력.\n\n"
    "종목명: 안국약품 (001540, KOSPI) / 업종: 의약품 / 산업: 제약"
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=200,
    temperature=0.3,
)
print(resp.choices[0].message.content.strip())
