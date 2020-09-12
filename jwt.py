"""JWT service."""
import logging

from django.contrib.auth import (
    get_user_model,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .otp import otp_service
from .user import user_service

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTService:
    """JWTService."""

    def create_token_for_user(self, user: User) -> dict:
        """Manually create JWT Token."""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def confirm_token(self, whatsapp: str, token: str) -> object:
        """Confirm token on registration."""
        user = user_service.get_by_whatsapp(whatsapp)

        if user:
            is_valid = otp_service.is_token_valid(user, token)

            if is_valid:
                return True
            else:
                logger.warn('Invalid token %s %s', whatsapp, token)

        else:
            logger.warn('Whatsapp number not found %s', whatsapp)

        return False


jwt_service = JWTService()
