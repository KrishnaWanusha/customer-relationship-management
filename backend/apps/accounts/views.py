from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from common.responses import api_error, api_success
from .serializers import LoginSerializer, UserSerializer
from .utils import delete_refresh_cookie, set_refresh_cookie


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return api_error(
                message="Invalid email or password.",
                errors=serializer.errors,
                status_code=400,
            )

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["org_id"] = user.organization_id

        data = {
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }

        response = api_success(data=data, message="Login successful")
        set_refresh_cookie(response, refresh)
        return response


class TokenRefreshCookieView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_NAME) or request.data.get("refresh")
        if not raw_refresh:
            return api_error(
                message="Refresh token is required.",
                status_code=400,
            )

        try:
            refresh = RefreshToken(raw_refresh)
            access = str(refresh.access_token)
        except (TokenError, InvalidToken):
            return api_error(
                message="Invalid or expired refresh token.",
                status_code=401,
            )

        response = api_success(
            data={"access": access},
            message="Token refreshed successfully",
        )

        if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS"):
            refresh.set_jti()
            refresh.set_exp()
            set_refresh_cookie(response, refresh)

        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = api_success(message="Logged out successfully")
        delete_refresh_cookie(response)
        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return api_success(data=serializer.data, message="User profile retrieved")
