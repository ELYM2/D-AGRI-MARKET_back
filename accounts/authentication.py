from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Permet d'authentifier via l'entete Authorization classique ou via
    le cookie HttpOnly depose par les vues d'authentification.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            try:
                return super().authenticate(request)
            except Exception as e:
                print(f"DEBUG AUTH: Header auth failed: {e}")
                return None

        raw_token = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        if raw_token is None:
            print(f"DEBUG AUTH: No cookie found. Cookies: {request.COOKIES.keys()}")
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception as e:
            print(f"DEBUG AUTH: Token validation failed: {e}")
            return None
