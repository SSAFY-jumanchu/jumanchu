import FinanceDataReader as fdr
from time import sleep

from .models import Stock
from .kis import get_access_token, get_stock_info
from .dart import get_financial_info
from .utils import get_corp_code_dict


def safe_float(val):
    try:
        return float(val) if val and val != "" else None
    except (ValueError, TypeError):
        return None


def get_stock_df():
    try:
        return fdr.StockListing('KOSPI')
    except:
        print("KOSPI 실패 → KRX 사용")
        return fdr.StockListing('KRX')


def collect_all_stocks():
    print("📊 주식 리스트 가져오는 중...")
    df = get_stock_df()

    print("🔑 KIS 토큰 발급...")
    token = get_access_token()

    print("🏢 DART corp_code 매핑...")
    corp_map = get_corp_code_dict()

    for _, row in df.iterrows():
        code = row['Code']
        name = row['Name']

        try:
            # ✅ 1. FDR (안정 데이터)
            market_cap = row.get("Marcap")

            # ✅ 2. KIS API
            kis_data = get_stock_info(token, code)

            # 👉 output / output1 둘 다 대응
            output = kis_data.get("output") or kis_data.get("output1") or {}

            # 👉 값 안전하게 가져오기
            per = safe_float(output.get("per"))
            pbr = safe_float(output.get("pbr"))
            eps = safe_float(output.get("eps"))
            bps = safe_float(output.get("bps"))
            beta = safe_float(output.get("beta"))

            # 👉 디버깅 (처음엔 켜두는거 추천)
            if not output:
                print(f"⚠️ KIS 데이터 없음: {code}")

            # ✅ 3. DART (지금은 연결만)
            corp_code = corp_map.get(code)
            
            if corp_code:
                fin = get_financial_info(corp_code)
                # 👉 아직 계산 안함 (다음 단계)
                # print(fin)

            # ✅ 4. DB 저장
            Stock.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "market_cap": market_cap,
                    "per": per,
                    "pbr": pbr,
                    "eps": eps,
                    "bps": bps,
                    "beta": beta
                }
            )

            print(f"✅ {name} 저장 완료")
            sleep(0.2)

        except Exception as e:
            print(f"❌ {code} 에러:", e)