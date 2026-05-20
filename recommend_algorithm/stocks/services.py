import sys
import FinanceDataReader as fdr
from time import sleep
import numpy as np
from datetime import datetime, timedelta
from .models import Stock, PrototypePool


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
    try:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=1095)).strftime('%Y-%m-%d')
        
        stock_df = fdr.DataReader(code, start_date, end_date)
        
        if stock_df.empty or len(stock_df) < 30:
            return None
            
        stock_df['return'] = stock_df['Close'].pct_change()
        
        df = stock_df[['return']].join(
            market_df[['return']], 
            lsuffix='_stock', 
            rsuffix='_market'
        ).dropna()
        
        if len(df) < 30:
            return None
        
        # ddof=1로 통일, cov_matrix[1][1]에서 분산 직접 추출
        cov_matrix = np.cov(df['return_stock'], df['return_market'])
        
        if cov_matrix[1][1] > 1e-10:
            return round(cov_matrix[0][1] / cov_matrix[1][1], 4)
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
        start_date = (datetime.today() - timedelta(days=1095)).strftime('%Y-%m-%d')
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

def calculate_beta_locally(code, market_df):
    """
    각 종목의 최근 3년 주가 데이터를 가져와서 
    미리 조회해 둔 KOSPI 시장 지수 수익률(market_df)과의 베타값을 연산합니다.
    """
    try:
        # 안전하게 0.1~0.2초 딜레이를 주어 대량 요청 시 차단되는 것을 방지합니다.
        sleep(0.15)
        
        # 최근 3년 데이터 기준 연산
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=1095)).strftime('%Y-%m-%d')
        
        stock_df = fdr.DataReader(code, start_date, end_date)
        if stock_df.empty or 'Close' not in stock_df.columns:
            return None
            
        stock_df['return'] = stock_df['Close'].pct_change()
        
        # 시장 수익률과 종목 수익률 결합
        df = stock_df[['return']].join(
            market_df[['return']], 
            lsuffix='_stock', 
            rsuffix='_market'
        ).dropna()
        
        # 영업일 기준 데이터가 너무 적으면 신뢰도가 낮으므로 패스
        if len(df) < 45:
            return None
            
        # 공분산(Covariance) 및 시장 분산(Variance) 계산
        cov = np.cov(df['return_stock'], df['return_market'])[0][1]
        var = np.var(df['return_market'])
        
        if var != 0:
            return round(cov / var, 4)
        return None
        
    except Exception as e:
        print(f"⚠️ {code} 종목 베타 연산 중 에러 발생: {e}")
        return None


def update_all_stocks_beta():
    """
    💡 [요청사항 반영] 
    프로토타입 Pool뿐만 아니라 DB에 존재하는 '모든 주식(Stock)'을 순회하며
    베타값을 연산하고 원본 마스터 테이블에 저장하는 함수입니다.
    """
    _ensure_utf8_stdout()
    print("📊 [마스터 테이블] 전체 주식 베타값 업데이트를 시작합니다...")

    # 1. 기준 시장 지수(KOSPI) 데이터 미리 딱 한 번만 조회
    print("📈 기준 시장 지수(KOSPI) 데이터 수집 중...")
    try:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=1095)).strftime('%Y-%m-%d')
        market_df = fdr.DataReader('KS11', start_date, end_date)
        market_df['return'] = market_df['Close'].pct_change()
    except Exception as e:
        print(f"❌ 코스피 지수 데이터 수집 실패로 인해 베타 계산을 중단합니다: {e}")
        return

    # 2. DB에 등록된 전체 주식(약 748개 이상) 가져오기
    all_stocks = Stock.objects.all()
    total_count = all_stocks.count()
    updated_count = 0

    print(f"🔄 총 {total_count}개 종목에 대한 전수 조사를 시작합니다.")

    # 3. 모든 종목을 순회하며 베타 연산 및 마스터 테이블 업데이트
    for idx, stock in enumerate(all_stocks, start=1):
        calculated_beta = calculate_beta_locally(stock.code, market_df)
        
        # 계산 결과가 있든 없든(None이든) 최신 상태로 갱신 (상장폐지나 데이터 부족 대응)
        stock.beta = calculated_beta
        stock.save(update_fields=['beta'])
        
        if calculated_beta is not None:
            updated_count += 1

            # 💡 [보너스 로직] 만약 이 종목이 프로토타입 Pool(Top 200 등)에도 속해 있다면 같이 업데이트
            pool_entry = PrototypePool.objects.filter(stock=stock).first()
            if pool_entry:
                pool_entry.beta = calculated_beta
                pool_entry.save(update_fields=['beta'])
        
        # 진행 상황 모니터링 로그
        if idx % 50 == 0 or idx == total_count:
            print(f"    진행 중... ({idx}/{total_count}) - 최근 완료 종목: {stock.name} (Beta: {stock.beta})")

    print(f"🎉 [완료] 전체 {total_count}개 중 {updated_count}개 종목의 베타값 업데이트 성공!")