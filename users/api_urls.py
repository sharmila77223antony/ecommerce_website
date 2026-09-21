from django.urls import path
from .views import RefreshTokenView
from .views import *


urlpatterns = [
    path("register/", register_user, name="register"),
    path("verify-otp/", verify_otp, name="verify-otp"),
    path("resend-otp/", resend_otp, name="resend-otp"),
    path("login/", login_user, name="login"),
    path("google-login/", GoogleLoginView.as_view(), name="google-login"),
    path(
        "refresh-token/",
        RefreshTokenView.as_view(),
        name="refresh-token"
    ),
]