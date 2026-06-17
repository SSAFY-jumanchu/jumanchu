from rest_framework import serializers

from accounts.models import InvestmentProfile, User


class InvestmentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentProfile
        fields = ['risk_type', 'investment_style', 'preferred_period', 'preferred_sector',
                  'risk_tolerance', 'investment_term', 'experience', 'loss_aversion', 'behavior',
                  'profiled_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = InvestmentProfileSerializer(source='investment_profile', read_only=True)
    profile_stock_code = serializers.CharField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'nickname', 'birth_year',
                  'profile', 'profile_stock_code', 'date_joined']
        read_only_fields = fields


class AccountSummarySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    balance = serializers.DecimalField(max_digits=15, decimal_places=0)
    initial_balance = serializers.DecimalField(max_digits=15, decimal_places=0)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class SignupRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(min_length=8, write_only=True)
    username = serializers.CharField(max_length=150)
    nickname = serializers.CharField(max_length=20)
    birth_year = serializers.IntegerField(min_value=1900)
    agree_terms = serializers.BooleanField()


class SignupResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    account = AccountSummarySerializer()


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    user = UserSerializer()


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class MeResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    has_completed_onboarding = serializers.BooleanField()


class MeUpdateRequestSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=20, required=False)
    birth_year = serializers.IntegerField(required=False, min_value=1900)


class OnboardingRequestSerializer(serializers.Serializer):
    """온보딩 설문 6문항(각 1/3/5점) + 관심섹터·보유기간. 5벡터는 서버에서 산출."""
    q1 = serializers.ChoiceField(choices=[1, 3, 5], help_text='투자 목적')
    q2 = serializers.ChoiceField(choices=[1, 3, 5], help_text='투자 경험')
    q3 = serializers.ChoiceField(choices=[1, 3, 5], help_text='손실 허용 범위')
    q4 = serializers.ChoiceField(choices=[1, 3, 5], help_text='자금 의존도')
    q5 = serializers.ChoiceField(choices=[1, 3, 5], help_text='투자 기간 (총점 가중 ×2)')
    q6 = serializers.ChoiceField(choices=[1, 3, 5], help_text='시장 하락 반응')
    preferred_sectors = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, default=list,
        help_text='관심 섹터 우선순위 순 (상위 3개 가중 1.0/0.6/0.3)',
    )
    preferred_period = serializers.IntegerField(
        required=False, min_value=1, allow_null=True, help_text='선호 보유 개월',
    )


class OnboardingResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    profile_stock = serializers.DictField(required=False, allow_null=True)
    welcome_bonus = serializers.DecimalField(max_digits=15, decimal_places=0)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
