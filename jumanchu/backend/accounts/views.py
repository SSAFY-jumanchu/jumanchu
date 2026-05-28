from decimal import Decimal

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import serializers as s
from accounts.models import InvestmentProfile
from accounts.services import calculate_investment_profile


def _stub():
    return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@extend_schema(tags=['Auth'])
class SignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='회원가입',
        request=s.SignupRequestSerializer,
        responses={201: s.SignupResponseSerializer},
    )
    def post(self, request):
        return _stub()


@extend_schema(tags=['Auth'])
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='로그인',
        request=s.LoginRequestSerializer,
        responses={200: s.LoginResponseSerializer},
    )
    def post(self, request):
        return _stub()


@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='로그아웃',
        request=None,
        responses={204: OpenApiResponse(description='No Content')},
    )
    def post(self, request):
        return _stub()


@extend_schema(tags=['Auth'])
class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='access 토큰 재발급 (refresh Cookie 사용)',
        request=None,
        responses={200: s.TokenRefreshResponseSerializer},
    )
    def post(self, request):
        return _stub()


@extend_schema(tags=['Auth'])
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='내 정보 조회',
        responses={200: s.MeResponseSerializer},
    )
    def get(self, request):
        return _stub()

    @extend_schema(
        summary='내 정보 수정',
        request=s.MeUpdateRequestSerializer,
        responses={200: s.MeResponseSerializer},
    )
    def patch(self, request):
        return _stub()


@extend_schema(tags=['Auth'])
class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='투자 성향 온보딩',
        request=s.OnboardingRequestSerializer,
        responses={200: s.OnboardingResponseSerializer},
    )
    def post(self, request):
        serializer = s.OnboardingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        survey_answers = data.get('survey_answers')
        score_breakdown = None
        risk_score = None

        if survey_answers:
            survey_result = calculate_investment_profile(survey_answers)
            risk_type = survey_result.risk_type
            risk_score = survey_result.risk_score
            risk_profile = survey_result.risk_label
            score_breakdown = survey_result.score_breakdown
        else:
            risk_type = data['risk_type']
            risk_profile = InvestmentProfile.RiskType(risk_type).label

        profile, _ = InvestmentProfile.objects.get_or_create(
            user=request.user,
            defaults={'risk_type': risk_type},
        )
        profile.risk_type = risk_type
        profile.risk_score = risk_score
        profile.survey_answers = survey_answers or {}
        profile.investment_style = data.get('investment_style') or profile.investment_style or risk_profile

        if 'preferred_period' in data:
            profile.preferred_period = data['preferred_period']
        if 'preferred_sector' in data:
            profile.preferred_sector = data['preferred_sector']

        profile.save()

        return Response({
            'user': s.UserSerializer(request.user).data,
            'profile_stock': None,
            'welcome_bonus': Decimal('0'),
            'risk_score': risk_score,
            'risk_profile': risk_profile,
            'score_breakdown': score_breakdown,
        })


@extend_schema(tags=['Auth'])
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='비밀번호 재설정 요청',
        request=s.PasswordResetRequestSerializer,
        responses={204: OpenApiResponse(description='No Content')},
    )
    def post(self, request):
        return _stub()
