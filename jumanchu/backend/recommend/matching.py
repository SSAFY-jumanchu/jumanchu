"""
온보딩 궁합 매칭 — 5벡터 × Stock DNA → match_score · signature(1등) · 4유형 라벨.

※ 정율(Algo) 도메인 산식을 BE가 임시 구현. 추후 recommend_algo로 분리.
산식 출처: docs/장투점수_산정로직.md §2 / ALGORITHM_DB_OPTIMIZATION_SPEC.jy.md §2-5③ + 온보딩 결과 화면 스펙.

⚠️ 리스크 항 스케일: 문서의 risk_tolerance/2.5는 1~5를 0~2로 보내 음수가 나는 오류로 보여,
   (x-1)/4로 0~1 정규화해 DNA(0~1)와 비교한다. 정율 확인 필요.
"""
from __future__ import annotations

from recommend.models import StockDna
from stocks.models import Stock

# 4유형 (위험축 × 기간축) → (이름, 이모지, 설명)
INVESTOR_TYPES = {
    ("공격", "장기"): ("성장 동반형", "🌱", "변동성 감수, 고성장주 장기 보유"),
    ("공격", "단기"): ("단기 승부형", "⚡", "모멘텀·테마를 짧고 굵게"),
    ("안정", "장기"): ("가치 파트너형", "🌳", "우량·저평가·배당주 장기 보유"),
    ("안정", "단기"): ("신중 탐색형", "🔍", "보수적으로 짧게 관망"),
}


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _norm5(v: int) -> float:
    """1~5 벡터 → 0~1 정규화."""
    return _clamp01((v - 1) / 4.0)


def _f(x) -> float:
    """DNA Decimal → float. null이면 중립 0.5."""
    return 0.5 if x is None else float(x)


def compute_match_score(profile, dna, sector_weights: dict) -> float:
    """유저 5벡터 × 종목 DNA → 궁합 점수 0~100."""
    vol, val, grw, sta = _f(dna.volatility), _f(dna.value_score), _f(dna.growth_score), _f(dna.stability)

    # 리스크 35% — 위험성향 ↔ 변동성
    risk_m = 1 - abs(_norm5(profile.risk_tolerance) - vol)

    # 기간 20% — 단기→변동 / 중기→(안정+가치+변동)/3 / 장기→(안정+가치)/2
    term = profile.investment_term
    if term <= 2:
        term_m = vol
    elif term == 3:
        term_m = (sta + val + vol) / 3
    else:
        term_m = (sta + val) / 2

    # 섹터 20% — 관심섹터면 가중치(1.0/0.6/0.3), 아니면 0.5
    sector_m = sector_weights.get(dna.sector, 0.5)

    # 경험 15% — 초보→안정 / 중급→(안정+성장)/2 / 숙련→(성장+변동)/2
    exp = profile.experience
    if exp <= 2:
        exp_m = sta
    elif exp == 3:
        exp_m = (sta + grw) / 2
    else:
        exp_m = (grw + vol) / 2

    # 스타일 10% — 종목 가치·성장 (추후 behavior 반영)
    style_m = (val + grw) / 2

    total = (
        _clamp01(risk_m) * 0.35
        + _clamp01(term_m) * 0.20
        + _clamp01(sector_m) * 0.20
        + _clamp01(exp_m) * 0.15
        + _clamp01(style_m) * 0.10
    ) * 100
    return round(total, 1)


LARGE_CAP_TOP_N = 200


def _large_cap_ids(top_n: int) -> set:
    """시장(KRW/USD)별 market_cap 상위 top_n 종목 id. 잡주·외국증권 배제용."""
    ids = set()
    for currency in ("KRW", "USD"):
        ids.update(
            Stock.objects.filter(is_active=True, currency=currency, market_cap__isnull=False)
            .order_by("-market_cap").values_list("id", flat=True)[:top_n]
        )
    return ids


def find_signature(profile, sector_weights: dict, top_sector: str | None = None, top_n: int = LARGE_CAP_TOP_N):
    """대형주(market_cap 상위 top_n) 중 궁합 1등 종목.

    1순위 관심섹터(top_sector)가 있으면 그 섹터 내 궁합 1등을 우선,
    해당 섹터에 대형주 후보가 없거나 관심섹터 미선택이면 전체 1등으로 폴백.
    → (StockDna, score) | (None, None).
    """
    calc_date = (StockDna.objects.order_by("-calculated_date")
                 .values_list("calculated_date", flat=True).first())
    if calc_date is None:
        return None, None
    candidates = _large_cap_ids(top_n)
    qs = StockDna.objects.filter(calculated_date=calc_date, stock_id__in=candidates).select_related("stock")

    best = best_sector = None
    best_score = best_sector_score = -1.0
    for dna in qs:
        score = compute_match_score(profile, dna, sector_weights)
        if score > best_score:
            best, best_score = dna, score
        if top_sector and dna.sector == top_sector and score > best_sector_score:
            best_sector, best_sector_score = dna, score

    if best_sector is not None:
        return best_sector, best_sector_score
    return best, best_score


def classify_investor_type(profile) -> dict:
    """5벡터 → 4유형 라벨 + 경험 배지."""
    risk_axis = (profile.risk_tolerance + profile.behavior) / 2
    risk_lab = "공격" if risk_axis >= 3 else "안정"
    term_lab = "장기" if profile.investment_term >= 3 else "단기"
    name, emoji, desc = INVESTOR_TYPES[(risk_lab, term_lab)]

    exp = profile.experience
    if exp <= 2:
        badge_emoji, badge = "🐣", "입문"
    elif exp == 3:
        badge_emoji, badge = "🐤", "중급"
    else:
        badge_emoji, badge = "🦅", "숙련"

    return {
        "type": name,
        "emoji": emoji,
        "description": desc,
        "experience_level": badge,
        "experience_emoji": badge_emoji,
        "label": f"{badge_emoji} {badge} · {emoji} {name}",
    }
