from rest_framework import serializers

from accounts.models import InvestmentProfile, User
from accounts.services import ANSWER_SCORES


class InvestmentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentProfile
        fields = ['risk_type', 'risk_score', 'survey_answers',
                  'investment_style', 'preferred_period',
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


class SurveyAnswersSerializer(serializers.Serializer):
    q1 = serializers.IntegerField(min_value=1, max_value=5)
    q2 = serializers.IntegerField(min_value=1, max_value=5)
    q3 = serializers.IntegerField(min_value=1, max_value=5)
    q4 = serializers.IntegerField(min_value=1, max_value=5)
    q5 = serializers.IntegerField(min_value=1, max_value=5)
    q6 = serializers.IntegerField(min_value=1, max_value=5)

    def validate(self, attrs):
        invalid_questions = [
            key for key, value in attrs.items()
            if int(value) not in ANSWER_SCORES
        ]
        if invalid_questions:
            raise serializers.ValidationError({
                key: '1, 3, 5 중 하나를 입력해주세요.'
                for key in invalid_questions
            })
        return {key: int(value) for key, value in attrs.items()}


class OnboardingRequestSerializer(serializers.Serializer):
    survey_answers = SurveyAnswersSerializer(required=False)
    risk_type = serializers.ChoiceField(
        choices=InvestmentProfile.RiskType.choices,
        required=False,
    )
    investment_style = serializers.CharField(max_length=50, required=False, allow_blank=True)
    preferred_period = serializers.IntegerField(required=False, min_value=1)
    preferred_sector = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get('survey_answers') and not attrs.get('risk_type'):
            raise serializers.ValidationError(
                'survey_answers 또는 risk_type 중 하나는 필요합니다.'
            )
        return attrs


class OnboardingResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    profile_stock = serializers.DictField(required=False, allow_null=True)
    welcome_bonus = serializers.DecimalField(max_digits=15, decimal_places=0)
    risk_score = serializers.IntegerField(required=False, allow_null=True)
    risk_profile = serializers.CharField(required=False)
    score_breakdown = serializers.DictField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True,
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
