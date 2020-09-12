"""Auth service."""
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .otp import otp_service
from .whatsapp import whatsapp_service

User = get_user_model()


class AuthService:
    """AuthService."""

    def send_login_otp(self, user_id: uuid.UUID) -> tuple:
        """Login user.

        Send whatsapp OTP
        This function should be run async as it takes a while to send whatsapp
        """
        user = User.objects.get(pk=user_id)
        token, flag = otp_service.get_login_token(user)

        message = settings.BOLU_OTP_LOGIN_TEMPLATE.format(code=token.code)
        to = str(user.whatsapp)
        response = whatsapp_service.send_message(to, message)
        token.sent_at = timezone.now()
        token_status = otp_service.get_wa_send_message_status(response)
        token.sent_status = token_status
        token.save()

        return token

    def can_login(self, user: User) -> bool:
        """Check whether user can login."""
        if user and user.is_active:
            return True

        return False


auth_service = AuthService()
