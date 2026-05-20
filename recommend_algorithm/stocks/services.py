import sys
import FinanceDataReader as fdr
from time import sleep
import numpy as np
from datetime import datetime, timedelta


def _ensure_utf8_stdout():
    """Windows cp949 환경에서 이모지 출력 시 발생하는 UnicodeEncodeError 방지"""
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python 3.6 이하에서는 reconfigure 미지원

from .models import Stock,PrototypePool
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

            # 👉 값 안전하게 가져오기 (beta 삭제)
            per = safe_float(output.get("per"))
            pbr = safe_float(output.get("pbr"))
            eps = safe_float(output.get("eps"))
            bps = safe_float(output.get("bps"))

            # 👉 디버깅 (처음엔 켜두는거 추천)
            if not output:
                print(f"⚠️ KIS 데이터 없음: {code}")

            # ✅ 3. DART (지금은 연결만)
            corp_code = corp_map.get(code)
            
            if corp_code:
                fin = get_financial_info(corp_code)
                # 👉 아직 계산 안함 (다음 단계)
                # print(fin)

            # ✅ 4. DB 저장 (defaults에서 beta 필드 제거)
            Stock.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "market_cap": market_cap,
                    "per": per,
                    "pbr": pbr,
                    "eps": eps,
                    "bps": bps,
                }
            )
            print(f"✅ {name}({code}) 적재 완료 (시총: {market_cap}, PER: {per})")
            
            # API 과부하 및 제한 예방을 위한 타임 슬립
            sleep(0.1)

        except Exception as e:
            print(f"❌ {name}({code}) 적재 중 에러 발생: {e}")

def calculate_beta_locally(code, market_df):
    """
    FinanceDataReader 데이터를 기반으로 최근 1개년 동안의 
    KOSPI 지수 대비 개별 종목의 통계적 베타(Beta)를 계산합니다.
    """
    try:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 개별 종목 주가 가져오기
        stock_df = fdr.DataReader(code, start_date, end_date)
        
        if stock_df.empty or len(stock_df) < 30:
            return None
            
        stock_df['return'] = stock_df['Close'].pct_change()
        
        # 날짜 기준으로 시장 지수와 결합
        df = stock_df[['return']].join(
            market_df[['return']], 
            lsuffix='_stock', 
            rsuffix='_market'
        ).dropna()
        
        if len(df) < 30:
            return None
            
        # 공분산 및 분산 연산
        cov = np.cov(df['return_stock'], df['return_market'])[0][1]
        var = np.var(df['return_market'])
        
        if var != 0:
            return round(cov / var, 4)
        return None
        
    except Exception as e:
        print(f"⚠️ {code} 베타 연산 실패: {e}")
        return None


def update_prototype_pool_beta():
    """
    PrototypePool에 등록된 모든 종목(상위 200개 등)의
    로컬 베타값을 계산하여 Stock 마스터 테이블과 PrototypePool 테이블에 반영합니다.
    """
    _ensure_utf8_stdout()
    # 1. PrototypePool에 있는 종목 가져오기
    pool_entries = PrototypePool.objects.select_related('stock').all()
    
    if not pool_entries.exists():
        print("⚠️ PrototypePool 데이터가 비어 있습니다. 먼저 프로토타입 풀 적재 로직을 실행해 주세요.")
        return

    # 현재 풀에 몇 개가 들어있는지 동적으로 파악 (예: 200개)
    pool_count = pool_entries.count()
    print(f"🔄 현재 PrototypePool에 등록된 {pool_count}개 종목의 베타 계산을 시작합니다...")

    # 2. 기준 시장 지수(KOSPI) 1년치 데이터 미리 딱 한 번만 조회
    print("📈 기준 시장 지수(KOSPI) 데이터 수집 중...")
    try:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        market_df = fdr.DataReader('KS11', start_date, end_date)
        market_df['return'] = market_df['Close'].pct_change()
    except Exception as e:
        print(f"❌ 코스피 지수 데이터 수집 실패로 인해 베타 계산을 중단합니다: {e}")
        return

    # 3. 풀에 있는 모든 종목(200개) 순회하며 베타 연산 및 업데이트
    updated_count = 0
    for entry in pool_entries:
        stock = entry.stock  # Stock 마스터 객체 접근
        
        # 베타 연산 함수 호출 (기존에 만들어 두신 함수)
        calculated_beta = calculate_beta_locally(stock.code, market_df)
        
        if calculated_beta is not None:
            # Stock 마스터 테이블의 beta 필드 업데이트
            stock.beta = calculated_beta
            stock.save(update_fields=['beta'])
            
            # PrototypePool 테이블의 beta 필드도 함께 업데이트 (100위 이후 포함 전체 적용)
            entry.beta = calculated_beta
            entry.save(update_fields=['beta'])
            
            updated_count += 1
            print(f"✅ [{stock.name}({stock.code})] 베타 계산 완료: {calculated_beta}")
        else:
            print(f"⚠️ [{stock.name}({stock.code})] 데이터 부족 등으로 베타 계산 스킵")

    print(f"🎉 완료: 총 {pool_count}개 중 {updated_count}개 종목의 베타 값이 성공적으로 갱신되었습니다!")


# update_betas.py management command에서 호출하는 이름과 맞추기 위한 별칭
update_prototype_pool_betas = update_prototype_pool_beta