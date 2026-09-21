from rest_framework import serializers

from developer.models import User


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