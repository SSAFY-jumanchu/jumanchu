from django.test import TestCase

# TODO(auth): 인증 플로우 단위 테스트 (rest_framework.test.APIClient 사용)
#   - 회원가입 성공 + portfolio.Account 자동 생성 검증
#   - 로그인 → access 발급 + refresh 쿠키 Set-Cookie 검증
#   - 인증 없이 /me/ → 401
#   - access 토큰으로 /me/ → 200
#   - /token/refresh/ 회전 동작 (새 access + 새 refresh 쿠키)
#   - logout 후 같은 refresh 재사용 차단 (blacklist)
#   - 중복 nickname → 409
