from django.conf import settings


def _cookie_params(max_age: int | None = None):
    return {
        "domain": settings.AUTH_COOKIE_DOMAIN or None,
        "secure": settings.AUTH_COOKIE_SECURE,
        "httponly": True,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "path": "/",
        "max_age": max_age,
    }


def set_jwt_cookies(response, access: str | None = None, refresh: str | None = None):
    if access:
        response.set_cookie(
            settings.ACCESS_TOKEN_COOKIE_NAME,
            access,
            **_cookie_params(int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())),
        )
    if refresh:
        response.set_cookie(
            settings.REFRESH_TOKEN_COOKIE_NAME,
            refresh,
            **_cookie_params(int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())),
        )


def clear_jwt_cookies(response):
    response.delete_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        domain=settings.AUTH_COOKIE_DOMAIN or None,
        path="/",
    )
    response.delete_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        domain=settings.AUTH_COOKIE_DOMAIN or None,
        path="/",
    )
