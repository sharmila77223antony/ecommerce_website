from rest_framework import serializers

from developer.models import *


class RegisterSerializer(serializers.Serializer):

    name = serializers.CharField(
        max_length=150,
        required=True
    )

    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        required=True
    )

    email = serializers.EmailField(
        required=True
    )

    phone = serializers.CharField(
        min_length=10,
        max_length=15,
        required=True
    )

    def validate_name(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Name cannot be empty."
            )

        if not all(
            character.isalpha() or character.isspace()
            for character in value
        ):
            raise serializers.ValidationError(
                "Name can contain only letters and spaces."
            )

        return value

    def validate_email(self, value):

        value = value.lower().strip()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already registered."
            )

        return value

    def validate_phone(self, value):

        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits."
            )

        return value

    def validate_password(self, value):

        if value.isalpha():
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        if value.isdigit():
            raise serializers.ValidationError(
                "Password must contain letters and numbers."
            )

        return value

class VerifyOTPSerializer(serializers.Serializer):

    email = serializers.EmailField(
        required=True
    )

    otp = serializers.CharField(
        min_length=6,
        max_length=6,
        required=True
    )

    def validate_email(self, value):
        return value.lower().strip()

    def validate_otp(self, value):

        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain only numbers."
            )

        return value

class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField(
        required=True
    )

    password = serializers.CharField(
        required=True,
        write_only=True
    )

    def validate_email(self, value):
        return value.lower().strip()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.lower().strip()


class ForgotPasswordVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
        required=True
    )

    def validate_email(self, value):
        return value.lower().strip()

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain only numbers."
            )

        return value


class ResetPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)

    new_password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        required=True
    )

    confirm_password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        required=True
    )

    def validate_email(self, value):
        return value.lower().strip()

    def validate_new_password(self, value):

        if value.isalpha():
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        if value.isdigit():
            raise serializers.ValidationError(
                "Password must contain letters and numbers."
            )

        return value

    def validate(self, data):

        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        return data

class ChangePasswordSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)

    current_password = serializers.CharField(
        required=True,
        write_only=True
    )

    new_password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=True,
        write_only=True
    )

    confirm_password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=True,
        write_only=True
    )

    def validate_email(self, value):
        return value.lower().strip()

    def validate_new_password(self, value):

        if value.isalpha():
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        if value.isdigit():
            raise serializers.ValidationError(
                "Password must contain letters and numbers."
            )

        return value

    def validate(self, data):

        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        if data["current_password"] == data["new_password"]:
            raise serializers.ValidationError({
                "new_password": "New password must be different from current password."
            })

        return data

class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    icon = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "icon",
        ]

    def get_icon(self, obj):
        request = self.context.get("request")

        if obj.icon:
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url

        return None


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(
        many=True,
        read_only=True
    )

    icon = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "icon",
            "subcategories",
        ]

    def get_icon(self, obj):
        request = self.context.get("request")

        if obj.icon:
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url

        return None