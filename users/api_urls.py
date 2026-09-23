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
    path( "forgot-password/", forgot_password, name="forgot-password" ), 
    path( "forgot-password/resend-otp/", resend_forgot_password_otp, name="resend-forgot-password-otp" ), 
    path( "forgot-password/verify-otp/", verify_forgot_password_otp, name="verify-forgot-password-otp" ),
    path(
        "forgot-password/reset/",
        reset_password,
        name="reset-password"
    ),
    path(
        "change-password/",
        change_password,
        name="change-password"
    ),
    path(
        "categories/",
        CategoryListAPIView.as_view(),
        name="category-list"
    ),
    path(
        "subcategories/",
        SubCategoryListAPIView.as_view(),
        name="subcategory-list"
    ),
    path(
        "products/",
        ProductListAPIView.as_view(),
        name="product-list"
    ),
    path(
        "featured/",
        FeaturedProductListAPIView.as_view(),
        name="featured-product-list"
    ),
    path(
        "products/<uuid:product_id>/",
        ProductDetailAPIView.as_view(),
        name="product-detail"
    ),
]