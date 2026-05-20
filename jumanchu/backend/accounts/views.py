from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import serializers as s


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
        return _stub()


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
