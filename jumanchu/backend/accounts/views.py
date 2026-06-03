from accounts.serializers import LoginRequestSerializer
from datetime import date
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from accounts import serializers as s
from accounts.models import User, InvestmentProfile
from portfolio.models import Account
from stocks.models import Stock
from stocks.serializers import StockSerializer
from decimal import Decimal



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
    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST'))
    def post(self, request):
        if getattr(request, 'limited', False):
            return Response({'detail': '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        # TODO(auth): 회원가입 구현
        #   1. SignupRequestSerializer 로 입력 검증
        serializer = s.SignupRequestSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
        #   2. password == password_confirm 확인 (불일치 → 400)
            if data['password'] != data['password_confirm']:
                return Response({'detail': '비밀번호가 일치하지 않습니다.'},
                                status=status.HTTP_400_BAD_REQUEST)
            
        #   3. birth_year 로 만 14세 이상 확인 (미달 → 400)
            if date.today().year - data['birth_year'] < 14:
                return Response({'detail': '만 14세 이상만 가입할 수 있습니다.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(username=data['username']).exists():
                return Response({'detail': '이미 사용 중인 아이디입니다.'},
                            status=status.HTTP_409_CONFLICT)
            if User.objects.filter(email=data['email']).exists():
                return Response({'detail': '이미 사용 중인 이메일입니다.'},
                                status=status.HTTP_409_CONFLICT)
            if User.objects.filter(nickname=data['nickname']).exists():
                return Response({'detail': '이미 사용 중인 닉네임입니다.'},
                                status=status.HTTP_409_CONFLICT)
            #   4. @transaction.atomic 안에서:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=data['email'],
                    username=data['email'],
                    nickname=data['nickname'],
                    birth_year=data['birth_year'],
                    password=data['password'],
                )
                account = Account.objects.create(user=user)

            response = s.SignupResponseSerializer({'user':user, 'account':account})
            return Response(response.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Auth'])
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='로그인',
        request=s.LoginRequestSerializer,
        responses={200: s.LoginResponseSerializer},
    )
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def post(self, request):
        if getattr(request, 'limited', False):
            return Response({'detail': '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        #   1. LoginRequestSerializer 검증 → email/password 인증 (실패 → 401)
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        user = User.objects.filter(email=data['email']).first()
        if user is None or not user.check_password(data['password']):
            return Response({'detail' : '이메일 또는 비밀번호가 올바르지 않습니다.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({'detail' : '비활성화된 계정입니다.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        #   2. RefreshToken.for_user(user) 로 refresh/access 발급
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        #   3. LoginResponseSerializer 로 200 {access, user}
        body = s.LoginResponseSerializer({'access':access, 'user':user})
        response = Response(body.data, status=status.HTTP_200_OK)
        #   4. response.set_cookie(SIMPLE_JWT['AUTH_COOKIE'], str(refresh), ...)
        #        httponly / secure / samesite='Strict' / path=AUTH_COOKIE_PATH / max_age=14일
        jwt = settings.SIMPLE_JWT
        response.set_cookie(
            key=jwt['AUTH_COOKIE'],
            value=str(refresh),
            httponly=jwt['AUTH_COOKIE_HTTP_ONLY'],
            secure=jwt['AUTH_COOKIE_SECURE'],
            samesite=jwt['AUTH_COOKIE_SAMESITE'],
            path=jwt['AUTH_COOKIE_PATH'],
            max_age=int(jwt['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        )
        return response


@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='로그아웃',
        request=None,
        responses={204: OpenApiResponse(description='No Content')},
    )
    def post(self, request):
        #   1. request.COOKIES.get(AUTH_COOKIE) 로 refresh 읽기
        cookie_name = settings.SIMPLE_JWT['AUTH_COOKIE']
        cookie_path = settings.SIMPLE_JWT['AUTH_COOKIE_PATH']

        refresh = request.COOKIES.get(cookie_name)

        #   2. RefreshToken(refresh).blacklist()  (token_blacklist 앱 필요)
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass

        #   3. 204 응답 + response.delete_cookie(AUTH_COOKIE, path=AUTH_COOKIE_PATH)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(cookie_name, path=cookie_path)
        return response


@extend_schema(tags=['Auth'])
class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='access 토큰 재발급 (refresh Cookie 사용)',
        request=None,
        responses={200: s.TokenRefreshResponseSerializer},
    )
    def post(self, request):
        cookie_name = settings.SIMPLE_JWT['AUTH_COOKIE']
        cookie_path = settings.SIMPLE_JWT['AUTH_COOKIE_PATH']

        # 1) 쿠키에서 refresh 읽기 (없으면 401)
        raw = request.COOKIES.get(cookie_name)
        if not raw:
            return Response({'detail': 'refresh 토큰이 없습니다.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        # 2) refresh 검증 — 만료/무효/블랙리스트(로그아웃됨)면 TokenError → 401
        #    RefreshToken()은 생성 시점에 서명·만료·블랙리스트를 모두 확인함
        try:
            refresh = RefreshToken(raw)
        except TokenError:
            return Response({'detail': 'refresh 토큰이 유효하지 않습니다.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        # 3) 새 access 발급 (회전 전에 먼저 뽑음)
        access = refresh.access_token

        # 4) 회전: 기존 refresh를 blacklist → 같은 객체를 새 jti/exp/iat로 갱신 = 새 refresh
        #    (ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION 설정을 코드로 구현한 것)
        try:
            refresh.blacklist()          # 옛 refresh 무효화 (token_blacklist 테이블 필요)
        except AttributeError:
            pass                         # blacklist 앱 없을 때 방어 (지금은 설치돼 있음)
        refresh.set_jti()                # 새 식별자
        refresh.set_exp()                # 만료 14일 재설정
        refresh.set_iat()                # 발급시각 재설정

        # 5) 200 {access} + 새 refresh를 다시 쿠키로
        body = s.TokenRefreshResponseSerializer({'access': str(access)}).data
        response = Response(body, status=status.HTTP_200_OK)
        response.set_cookie(
            key=cookie_name,
            value=str(refresh),          # ← 회전된 '새' refresh
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path=cookie_path,
        )
        return response


@extend_schema(tags=['Auth'])
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='내 정보 조회',
        responses={200: s.MeResponseSerializer},
    )
    def get(self, request):
        #   - request.user 직렬화 + has_completed_onboarding (= investment_profile 존재 여부)
        data = {
            'user' : request.user,
            'has_completed_onboarding' : hasattr(request.user, 'investment_profile'),
        }
        serializer = s.MeResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary='내 정보 수정',
        request=s.MeUpdateRequestSerializer,
        responses={200: s.MeResponseSerializer},
    )
    def patch(self, request):
        #   - MeUpdateRequestSerializer(partial) 로 nickname/birth_year 검증
        serializer = s.MeUpdateRequestSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user

        new_nickname = data.get('nickname')
        if new_nickname and User.objects.filter(nickname=new_nickname).exclude(pk=user.pk).exists():
            return Response({'detail' : '이미 사용 중인 닉네임입니다.'},
                            status=status.HTTP_409_CONFLICT)

        for field, value in data.items():
            setattr(user, field, value)
        user.save()

        body = {
            'user':user,
            'has_completed_onboarding':hasattr(user, 'investment_profile'),
        }
        response = s.MeResponseSerializer(body)
        return Response(response.data, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth'])
class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='투자 성향 온보딩',
        request=s.OnboardingRequestSerializer,
        responses={200: s.OnboardingResponseSerializer},
    )
    def post(self, request):
        # TODO(auth): 투자성향 온보딩
        #   1. OnboardingRequestSerializer 검증
        #   2. InvestmentProfile upsert (update_or_create, user=request.user)
        #   3. profile_stock: birth_year=상장연도 매칭 — stocks 데이터 의존, 없으면 null
        #   4. welcome_bonus: Account.balance 에 가산 (금액은 ERD/팀 확인 후 확정)
        #   5. OnboardingResponseSerializer 로 200
        return _stub()


@extend_schema(tags=['Auth'])
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='비밀번호 재설정 요청',
        request=s.PasswordResetRequestSerializer,
        responses={204: OpenApiResponse(description='No Content')},
    )
    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST'))
    def post(self, request):
        if getattr(request, 'limited', False):
            return Response({'detail': '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        serializer = s.PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid()
        
        # 이번 범위에선 실제 발송 없음 (후속 이슈).
        # ⚠️ 이메일 가입 여부와 '무관하게' 항상 204 → 계정 존재 노출(enumeration) 방지.
        # 나중에 구현 시: 가입된 이메일이면 재설정 토큰 생성 후 메일 발송,
        #               아니면 아무것도 안 함. 단 응답은 두 경우 모두 204로 동일하게.
        return Response(status=status.HTTP_204_NO_CONTENT)

