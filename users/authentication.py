from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from developer.models import User


class CustomerJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):
        try:
            user_id = validated_token["user_id"]
        except KeyError:
            raise AuthenticationFailed(
                "Token contained no recognizable user identification"
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return user