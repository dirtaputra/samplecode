"""Otp Service."""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import pyotp

from bolu.models import OTPToken

logger = logging.getLogger(__name__)
User = get_user_model()


class OTPService:
    """OTPService class."""

    FLAG_OLD = 'OLD'
    FLAG_NEW = 'NEW'

    def get_valid_unverified_token(self, user: User, event: OTPToken.Event) -> OTPToken:
        """Get valid token but not verified."""
        tokens = OTPToken.objects.filter(
            user=user,
            verified_at=None,
            event=event,
        )
        now = timezone.now()
        valid_token = None

        for token in tokens:
            delta = now - token.created_at
            if delta.total_seconds() <= token.interval:
                valid_token = token
                break

        return valid_token

    def create_new_token(self, user: User, event: OTPToken.Event) -> OTPToken:
        """Create new token."""
        now = timezone.now()
        secret = pyotp.random_base32()
        interval = settings.BOLU_OTP_EXPIRE
        totp = pyotp.TOTP(
            secret,
            digits=settings.BOLU_OTP_LENGTH,
            interval=interval,
        )
        code = totp.at(now)
        token = OTPToken.objects.create(
            secret=secret,
            code=code,
            interval=interval,
            created_at=now,
            event=event,
            user=user,
        )

        return token

    def get_registration_token(self, user: User) -> tuple:
        """Get registration token."""
        token = self.get_valid_unverified_token(user, OTPToken.Event.REGISTRATION)
        flag = self.FLAG_OLD

        if not token:
            token = self.create_new_token(user, OTPToken.Event.REGISTRATION)
            flag = self.FLAG_NEW

        return token, flag

    def get_login_token(self, user: User):
        """Get login token."""
        token = self.get_valid_unverified_token(user, OTPToken.Event.LOGIN)
        flag = self.FLAG_OLD

        if not token:
            token = self.create_new_token(user, OTPToken.Event.LOGIN)
            flag = self.FLAG_NEW

        return token, flag

    def is_token_valid(self, user: User, token: str):
        """Validate confirmation token on a number."""
        otp_token = OTPToken.objects.filter(
            user=user,
            code=token,
            verified_at__isnull=True,
        ).first()

        if otp_token:
            totp = pyotp.TOTP(
                otp_token.secret,
                digits=settings.BOLU_OTP_LENGTH,
                interval=settings.BOLU_OTP_EXPIRE,
            )
            is_valid = totp.verify(token, for_time=otp_token.created_at)

            if is_valid:
                otp_token.verified_at = timezone.now()
                otp_token.save()
                return True

            logger.warning('Token is not valid %s', token)
        else:
            logger.warning('OTPToken not found or verified already %s %s', user.whatsapp, token)

        return False

    def get_wa_send_message_status(self, response: str) -> OTPToken.SentStatus:
        """Parse string response status to OTPToken SentStatus."""
        response = response.lower() if response else ''
        status = OTPToken.SentStatus.UNSET

        if 'success' in response:
            status = OTPToken.SentStatus.SUCCESS
        elif 'phone_offline' in response:
            status = OTPToken.SentStatus.OFFLINE
        elif 'not found' in response:
            status = OTPToken.SentStatus.NOT_FOUND

        return status


otp_service = OTPService()
