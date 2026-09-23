import random
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from developer.models import *
from .serializers import *
from .utils import *
import requests
from rest_framework.views import APIView
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework_simplejwt.tokens import AccessToken, TokenError


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):

    serializer = RegisterSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            {
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    data = serializer.validated_data

    name = data["name"]
    password = data["password"]
    email = data["email"]
    phone = data["phone"]

    # Generate 6 digit OTP
    otp = str(
        random.randint(100000, 999999)
    )

    # Hash password before storing it
    hashed_password = make_password(password)

    # Store registration data temporarily
    cache.set(
        f"register_{email}",
        {
            "name": name,
            "password": hashed_password,
            "email": email,
            "phone": phone,
            "otp": otp,
        },
        timeout=600
    )

    # Send OTP
    email_sent = send_otp_email(
        email,
        otp,name
    )

    if not email_sent:

        cache.delete(
            f"register_{email}"
        )

        return Response(
            {
                "message": "Failed to send OTP email."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            "message": "OTP has been sent to your email."
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):

    serializer = VerifyOTPSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            {
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data["email"]
    otp = serializer.validated_data["otp"]

    # Get temporary registration data
    registration_data = cache.get(
        f"register_{email}"
    )

    if not registration_data:

        return Response(
            {
                "message": "OTP expired or registration data not found."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check OTP
    if registration_data["otp"] != otp:

        return Response(
            {
                "message": "Invalid OTP."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user using the already hashed password
    user = User.objects.create(
        name=registration_data["name"],
        password=registration_data["password"],
        email=registration_data["email"],
        phone=registration_data["phone"]
    )

    # Create separate profile
    UserProfile.objects.create(
        user=user,
        name=user.name,
        email=user.email,
        phone=user.phone
    )
    refresh = RefreshToken()

    # Add user information to refresh token
    refresh["user_id"] = str(user.id)
    refresh["name"] = user.name
    refresh["email"] = user.email

    # Create access token
    access_token = refresh.access_token


    # Delete temporary registration data
    cache.delete(
        f"register_{email}"
    )

    return Response(
        {
            "message": "Email verified successfully. User profile created.",

            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "phone": user.phone
            },

            "tokens": {
                "access": str(access_token),
                "refresh": str(refresh)
            }
        },
        status=status.HTTP_201_CREATED
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):

    email = request.data.get("email")

    if not email:
        return Response(
            {
                "message": "Email is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    email = email.lower().strip()

    # Get existing registration data
    registration_data = cache.get(
        f"register_{email}"
    )

    if not registration_data:

        return Response(
            {
                "message": "Registration expired. Please register again."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check 2-minute resend cooldown
    resend_allowed = cache.get(
        f"otp_resend_{email}"
    )

    if resend_allowed:

        return Response(
            {
                "message": "Please wait 2 minutes before requesting a new OTP."
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Generate new 6 digit OTP
    otp = str(
        random.randint(100000, 999999)
    )

    # Update OTP in registration data
    registration_data["otp"] = otp

    # Keep the remaining registration data for 10 minutes
    cache.set(
        f"register_{email}",
        registration_data,
        timeout=600
    )

    # Start 2-minute resend cooldown
    cache.set(
        f"otp_resend_{email}",
        True,
        timeout=120
    )

    # Send new OTP
    email_sent = send_otp_email(
        email,
        otp,
        registration_data["name"]
    )

    if not email_sent:

        cache.delete(
            f"otp_resend_{email}"
        )

        return Response(
            {
                "message": "Failed to send OTP email."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            "message": "New OTP has been sent to your email."
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):

    serializer = LoginSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            {
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    # Find user by email
    try:

        user = User.objects.get(
            email=email
        )

    except User.DoesNotExist:

        return Response(
            {
                "message": "Invalid email or password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check hashed password
    if not check_password(
        password,
        user.password
    ):

        return Response(
            {
                "message": "Invalid email or password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Create refresh token
    refresh = RefreshToken()

    refresh["user_id"] = str(user.id)
    refresh["name"] = user.name
    refresh["email"] = user.email

    # Create access token
    access_token = refresh.access_token

    access_token["user_id"] = str(user.id)
    access_token["name"] = user.name
    access_token["email"] = user.email

    return Response(
        {
            "message": "Login successful.",

            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "phone": user.phone
            },

            "tokens": {
                "access": str(access_token),
                "refresh": str(refresh)
            }
        },
        status=status.HTTP_200_OK
    )

class GoogleLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        access_token = request.data.get("access_token")

        if not access_token:
            return Response(
                {"message": "Google access token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            google_response = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                params={
                    "access_token": access_token
                },
                timeout=10
            )

            if google_response.status_code != 200:
                return Response(
                    {"message": "Invalid Google access token."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            google_data = google_response.json()

            google_id = google_data.get("id")
            email = google_data.get("email")
            name = google_data.get("name", "")
            picture = google_data.get("picture", "")

            if not google_id:
                return Response(
                    {"message": "Google ID not found."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not email:
                return Response(
                    {"message": "Google email not found."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            email = email.lower().strip()

            # Check whether this Google account already exists
            profile = (
                UserProfile.objects
                .filter(google_id=google_id)
                .select_related("user")
                .first()
            )

            if profile:
                user = profile.user

            else:
                # Check existing user by email
                user = User.objects.filter(email=email).first()

                if user:

                    profile = UserProfile.objects.filter(
                        user=user
                    ).first()

                    if not profile:
                        profile = UserProfile.objects.create(
                            user=user,
                            name=user.name,
                            email=user.email,
                            phone=user.phone,
                            google_id=google_id,
                            profile_image_url=picture,
                            auth_provider="google"
                        )

                    else:
                        # Do not overwrite existing user information
                        if not profile.google_id:
                            profile.google_id = google_id

                        if not profile.profile_image_url and picture:
                            profile.profile_image_url = picture

                        profile.save()

                else:

                    user = User.objects.create(
                        name=name,
                        email=email,
                        phone="",
                        password=make_password(None)
                    )

                    profile = UserProfile.objects.create(
                        user=user,
                        name=name,
                        email=email,
                        phone="",
                        google_id=google_id,
                        profile_image_url=picture,
                        auth_provider="google"
                    )

            # Create JWT tokens
            refresh = RefreshToken()

            refresh["user_id"] = str(user.id)
            refresh["name"] = user.name
            refresh["email"] = user.email

            access = refresh.access_token

            access["user_id"] = str(user.id)
            access["name"] = user.name
            access["email"] = user.email

            return Response(
                {
                    "message": "Google login successful.",
                    "user": {
                        "id": str(user.id),
                        "name": user.name,
                        "email": user.email,
                        "phone": user.phone,
                        "image": profile.profile_image_url,
                        "auth_provider": profile.auth_provider
                    },
                    "tokens": {
                        "access": str(access),
                        "refresh": str(refresh)
                    }
                },
                status=status.HTTP_200_OK
            )

        except requests.exceptions.Timeout:

            return Response(
                {"message": "Google request timed out."},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.exceptions.RequestException:

            return Response(
                {"message": "Unable to connect to Google."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        except Exception as e:

            print("GOOGLE LOGIN ERROR:", str(e))

            return Response(
                {"message": "Something went wrong."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RefreshTokenView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        refresh_token = (
            request.data.get("refresh")
            or request.COOKIES.get("refresh_token")
        )

        if not refresh_token:
            return Response(
                {"error": "Refresh token missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)

            access_token = refresh.access_token

            # Keep your custom user data in the new access token
            if refresh.get("user_id"):
                access_token["user_id"] = refresh.get("user_id")

            if refresh.get("name"):
                access_token["name"] = refresh.get("name")

            if refresh.get("email"):
                access_token["email"] = refresh.get("email")

            return Response(
                {
                    "access": str(access_token),
                    "refresh": str(refresh)
                },
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):

    serializer = ForgotPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data["email"]

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"message": "No account found with this email."},
            status=status.HTTP_404_NOT_FOUND
        )

    otp = str(random.randint(100000, 999999))

    cache.set(
        f"forgot_password_{email}",
        {
            "otp": otp,
            "user_id": str(user.id),
        },
        timeout=600
    )

    email_sent = send_otp_email(
        email,
        otp,
        user.name
    )

    if not email_sent:
        cache.delete(f"forgot_password_{email}")

        return Response(
            {"message": "Failed to send OTP email."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            "message": "Password reset OTP has been sent to your email."
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_forgot_password_otp(request):

    serializer = ForgotPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data["email"]

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"message": "No account found with this email."},
            status=status.HTTP_404_NOT_FOUND
        )

    registration_data = cache.get(
        f"forgot_password_{email}"
    )

    if not registration_data:
        return Response(
            {
                "message": "Forgot password session expired. Please request OTP again."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    resend_allowed = cache.get(
        f"forgot_password_resend_{email}"
    )

    if resend_allowed:
        return Response(
            {
                "message": "Please wait 2 minutes before requesting a new OTP."
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    otp = str(random.randint(100000, 999999))

    registration_data["otp"] = otp

    cache.set(
        f"forgot_password_{email}",
        registration_data,
        timeout=600
    )

    cache.set(
        f"forgot_password_resend_{email}",
        True,
        timeout=120
    )

    email_sent = send_otp_email(
        email,
        otp,
        user.name
    )

    if not email_sent:

        cache.delete(
            f"forgot_password_resend_{email}"
        )

        return Response(
            {"message": "Failed to send OTP email."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            "message": "New password reset OTP has been sent to your email."
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_forgot_password_otp(request):

    serializer = ForgotPasswordVerifyOTPSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data["email"]
    otp = serializer.validated_data["otp"]

    forgot_password_data = cache.get(
        f"forgot_password_{email}"
    )

    if not forgot_password_data:
        return Response(
            {
                "message": "OTP expired. Please request a new OTP."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if forgot_password_data["otp"] != otp:
        return Response(
            {
                "message": "Invalid OTP."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    cache.set(
        f"forgot_password_verified_{email}",
        True,
        timeout=600
    )

    cache.delete(
        f"forgot_password_{email}"
    )

    cache.delete(
        f"forgot_password_resend_{email}"
    )

    return Response(
        {
            "message": "OTP verified successfully. You can now reset your password."
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):

    serializer = ResetPasswordSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data["email"]
    new_password = serializer.validated_data["new_password"]

    # Check whether OTP was successfully verified
    otp_verified = cache.get(
        f"forgot_password_verified_{email}"
    )

    if not otp_verified:
        return Response(
            {
                "message": "Please verify the OTP before resetting your password."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)

    except User.DoesNotExist:
        return Response(
            {
                "message": "User not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # Hash the new password
    user.password = make_password(new_password)

    user.save(update_fields=["password"])

    # Delete the verification status
    cache.delete(
        f"forgot_password_verified_{email}"
    )

    return Response(
        {
            "message": "Password reset successfully."
        },
        status=status.HTTP_200_OK
    )



@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def change_password(request):

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return Response(
            {
                "message": "Authorization token is required."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not auth_header.startswith("Bearer "):
        return Response(
            {
                "message": "Invalid authorization format."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    access_token = auth_header[7:].strip()

    try:
        token = AccessToken(access_token)

    except TokenError:
        return Response(
            {
                "message": "Invalid or expired access token."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    user_id = token.get("user_id")

    if not user_id:
        return Response(
            {
                "message": "User ID not found in access token."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        user = User.objects.get(
            pk=user_id
        )

    except EcommerceUser.DoesNotExist:
        return Response(
            {
                "message": "User not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ChangePasswordSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    current_password = serializer.validated_data[
        "current_password"
    ]

    new_password = serializer.validated_data[
        "new_password"
    ]

    if not check_password(
        current_password,
        user.password
    ):
        return Response(
            {
                "message": "Current password is incorrect."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    user.password = make_password(
        new_password
    )

    user.save(
        update_fields=["password"]
    )

    return Response(
        {
            "message": "Password changed successfully."
        },
        status=status.HTTP_200_OK
    )

class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.prefetch_related(
            "subcategories"
        ).all()

        serializer = CategorySerializer(
            categories,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "success": True,
                "message": "Categories fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class SubCategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        subcategories = SubCategory.objects.select_related(
            "category"
        ).all()

        serializer = SubCategorySerializer(
            subcategories,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "success": True,
                "message": "Subcategories fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )



class ProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        products = Product.objects.prefetch_related(
            "images"
        ).filter(
            is_active=True
        ).order_by("-created_at")

        serializer = ProductSerializer(
            products,
            many=True,
            context={
                "request": request
            }
        )

        return Response(
            {
                "success": True,
                "message": "Products fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class FeaturedProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        products = Product.objects.prefetch_related(
            "images"
        ).filter(
            is_active=True,
            featured=True
        ).order_by("-created_at")

        serializer = ProductSerializer(
            products,
            many=True,
            context={
                "request": request
            }
        )

        return Response(
            {
                "success": True,
                "message": "Featured products fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class ProductDetailAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, product_id):

        try:
            product = Product.objects.prefetch_related(
                "images"
            ).get(
                id=product_id,
                is_active=True
            )

        except Product.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Product not found",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductDetailSerializer(
            product,
            context={
                "request": request
            }
        )

        return Response(
            {
                "success": True,
                "message": "Product details fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )