"""Registration service."""
import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .otp import otp_service
from .user import user_service
from .whatsapp import whatsapp_service

logger = logging.getLogger(__name__)
User = get_user_model()


class RegistrationService:
    """RegistrationService class."""

    def send_wa_activation(self, user_id: uuid.UUID):
        """Send verification url to whatsapp.

        This function should be run async as it takes a while to send whatsapp
        """
        user = User.objects.get(pk=user_id)
        token, flag = otp_service.get_registration_token(user)

        if flag == otp_service.FLAG_NEW:
            message = settings.BOLU_OTP_REGISTRATION_TEMPLATE.format(code=token.code)
            to = str(user.whatsapp)
            response = whatsapp_service.send_message(to, message)
            token.sent_at = timezone.now()
            token_status = otp_service.get_wa_send_message_status(response)
            token.sent_status = token_status
            token.save()
        else:
            pass  # do we need to send whatsapp while old token still valid?

        return token

    def full_name_split(self, full_name):
        """Split full name."""
        split = full_name.split()
        if len(split) > 1:
            first_name, last_name = full_name.rsplit(" ", 1)
            return first_name, last_name
        else:
            first_name = full_name
            last_name = ''
            return first_name, last_name

    def register(self, data) -> User:
        """Register user."""
        user = user_service.get_by_whatsapp(data['whatsapp'])

        if not user:
            full_name = data['full_name']
            first_name, last_name = self.full_name_split(full_name)
            del data['full_name']
            del data['store_name']
            user = User(**data)
            user.first_name = first_name
            user.last_name = last_name
            user.username = data['email']
            user.is_active = False
            user.set_password(settings.BOLU_STANDARD_PASSWORD)
            user.save()

        return user

    def confirm_token(self, whatsapp: str, token: str) -> object:
        """Confirm token on registration."""
        user = user_service.get_by_whatsapp(whatsapp)

        if user:
            is_valid = otp_service.is_token_valid(user, token)

            if is_valid:
                user.is_active = True
                user.save()
                email=user.username
                return True
            else:
                logger.warn('Invalid token %s %s', whatsapp, token)

        else:
            logger.warn('Whatsapp number not found %s', whatsapp)

        return False


registration_service = RegistrationService()
