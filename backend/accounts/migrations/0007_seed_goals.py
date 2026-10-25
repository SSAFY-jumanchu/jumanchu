# -*- coding: utf-8 -*-
"""자산 마일스톤(Goal) 시드 — docs/자산마일스톤.md §4.

target_amount는 '수익(총자산-초기지급금)' 목표로 해석한다(1억 시드 고정이라 수익금액=수익률×1억).
sort_order(1~20)를 식별 키로 update_or_create → 멱등(이미 시드돼 있으면 최신값으로 갱신).
"""
from django.db import migrations

GOALS = [
    {"sort_order": 1, "name": "무선 이어폰 (에어팟 프로)", "target_amount": 350000, "badge_emoji": "🎧", "category": "electronics", "tier": 1, "description": "첫 출발! 이어폰 하나는 가뿐히 모았어요"},
    {"sort_order": 2, "name": "가정용 게임기 (스위치 2)", "target_amount": 600000, "badge_emoji": "🎮", "category": "electronics", "tier": 1, "description": "퇴근 후 한 판은 이미 사고도 남아요"},
    {"sort_order": 3, "name": "명품 지갑", "target_amount": 900000, "badge_emoji": "👛", "category": "luxury", "tier": 1, "description": "지갑 속 자산이 진짜 지갑값을 넘겼네요"},
    {"sort_order": 4, "name": "최신 스마트폰 (아이폰 17 Pro)", "target_amount": 1700000, "badge_emoji": "📱", "category": "electronics", "tier": 1, "description": "신상폰 풀옵션, 일시불 가능!"},
    {"sort_order": 5, "name": "일본 여행 (2인)", "target_amount": 2000000, "badge_emoji": "✈️", "category": "travel", "tier": 2, "description": "주말 도쿄, 지금 떠나도 돼요"},
    {"sort_order": 6, "name": "게이밍 데스크탑", "target_amount": 3500000, "badge_emoji": "🖥️", "category": "electronics", "tier": 2, "description": "풀세팅 본체 한 대 완성!"},
    {"sort_order": 7, "name": "명품 가방", "target_amount": 8000000, "badge_emoji": "👜", "category": "luxury", "tier": 2, "description": "드디어 '그 가방' 라인에 들어섰어요"},
    {"sort_order": 8, "name": "유럽 한 달 여행", "target_amount": 10000000, "badge_emoji": "🌍", "category": "travel", "tier": 2, "description": "한 달 살기, 통장이 허락합니다"},
    {"sort_order": 9, "name": "경차 (캐스퍼 · 모닝)", "target_amount": 14000000, "badge_emoji": "🚗", "category": "car", "tier": 3, "description": "내 첫 차, 출고 가능해요"},
    {"sort_order": 10, "name": "국산 준중형차 (아반떼)", "target_amount": 20000000, "badge_emoji": "🚙", "category": "car", "tier": 3, "description": "국민 준중형 한 대 값 도달!"},
    {"sort_order": 11, "name": "국산 중형 세단 (쏘나타)", "target_amount": 32000000, "badge_emoji": "🚘", "category": "car", "tier": 3, "description": "중형 세단 풀옵션까지 커버"},
    {"sort_order": 12, "name": "국산 SUV (싼타페 · 쏘렌토)", "target_amount": 45000000, "badge_emoji": "🚙", "category": "car", "tier": 3, "description": "패밀리 SUV 한 대, 현금 박치기 가능"},
    {"sort_order": 13, "name": "수입 엔트리카 (BMW 3 · 벤츠 C)", "target_amount": 65000000, "badge_emoji": "🏎️", "category": "car", "tier": 4, "description": "수입차 엔트리 라인 진입!"},
    {"sort_order": 14, "name": "결혼 자금 (예식 + 스드메)", "target_amount": 80000000, "badge_emoji": "💍", "category": "life", "tier": 4, "description": "인생 한 번의 큰 행사, 준비 완료"},
    {"sort_order": 15, "name": "전세 보증금 (수도권 소형)", "target_amount": 200000000, "badge_emoji": "🔑", "category": "realestate", "tier": 4, "description": "내 이름으로 된 집 열쇠가 보여요"},
    {"sort_order": 16, "name": "지방 소형 아파트", "target_amount": 300000000, "badge_emoji": "🏢", "category": "realestate", "tier": 4, "description": "지방 소형 아파트 한 채 값!"},
    {"sort_order": 17, "name": "수도권 아파트", "target_amount": 600000000, "badge_emoji": "🏘️", "category": "realestate", "tier": 5, "description": "수도권에 내 집 마련, 현실권 진입"},
    {"sort_order": 18, "name": "서울 중위가 아파트", "target_amount": 1200000000, "badge_emoji": "🏙️", "category": "realestate", "tier": 5, "description": "서울 아파트 한 채, 손에 닿았어요"},
    {"sort_order": 19, "name": "서울 평균 아파트 (전용 84㎡)", "target_amount": 1500000000, "badge_emoji": "🌆", "category": "realestate", "tier": 5, "description": "서울 평균 아파트값을 따라잡았어요"},
    {"sort_order": 20, "name": "강남 아파트 (국민평형)", "target_amount": 2600000000, "badge_emoji": "🏰", "category": "realestate", "tier": 5, "description": "강남 입성, 자산의 정점입니다"},
]


def seed_goals(apps, schema_editor):
    Goal = apps.get_model("accounts", "Goal")
    for g in GOALS:
        Goal.objects.update_or_create(
            sort_order=g["sort_order"],
            defaults={
                "name": g["name"],
                "target_amount": g["target_amount"],
                "badge_emoji": g["badge_emoji"],
                "badge_name": g["name"],
                "description": g["description"],
                "category": g["category"],
                "tier": g["tier"],
            },
        )


def unseed_goals(apps, schema_editor):
    Goal = apps.get_model("accounts", "Goal")
    Goal.objects.filter(sort_order__in=[g["sort_order"] for g in GOALS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_goal_category_goal_description_goal_tier_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_goals, unseed_goals),
    ]
