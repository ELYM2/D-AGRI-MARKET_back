from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
)
from .throttles import AuthRateThrottle
from .utils import set_jwt_cookies, clear_jwt_cookies


class RegisterView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Issue JWT tokens on register for convenience
        refresh = RefreshToken.for_user(user)
        data = {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        response = Response(data, status=status.HTTP_201_CREATED)
        set_jwt_cookies(response, data["access"], data["refresh"])
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("refresh") or request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if token:
            try:
                refresh = RefreshToken(token)
                refresh.blacklist()
            except Exception:
                pass
        response = Response(status=status.HTTP_205_RESET_CONTENT)
        clear_jwt_cookies(response)
        return response


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        if settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION", False):
            for token in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=token)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_jwt_cookies(response)
        return response


class CookieTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            set_jwt_cookies(response, response.data.get("access"), response.data.get("refresh"))
        return response


class CookieTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if "refresh" not in data:
            cookie_refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
            if cookie_refresh:
                data["refresh"] = cookie_refresh
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        set_jwt_cookies(response, serializer.validated_data.get("access"), serializer.validated_data.get("refresh"))
        return response
