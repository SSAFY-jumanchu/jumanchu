from rest_framework import serializers

from accounts.models import InvestmentProfile, User


class InvestmentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentProfile
        fields = ['risk_type', 'investment_style', 'preferred_period',
                  'preferred_sector', 'updated_at']


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
    risk_type = serializers.ChoiceField(choices=InvestmentProfile.RiskType.choices)
    investment_style = serializers.CharField(max_length=50, required=False, allow_blank=True)
    preferred_period = serializers.IntegerField(required=False, min_value=1)
    preferred_sector = serializers.CharField(max_length=50, required=False, allow_blank=True)


class OnboardingResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    profile_stock = serializers.DictField(required=False, allow_null=True)
    welcome_bonus = serializers.DecimalField(max_digits=15, decimal_places=0)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
