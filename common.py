"""Common service module."""
from .user import user_service
from django.conf import settings
from django.core import signing

class CommonService:
    """Common service."""

    def create_confirmation_sign(self, email, confirmation_code_id):
        """Create Encrypted message to confirmation email."""
        user = user_service.get_by_email(email)
        user_id = user.id.hex
        payload = (user_id, confirmation_code_id,)

        # Set salt
        salts = settings.BOLU_SALTS
        last_char_ascii = ord(user_id[-1])
        salt_index = last_char_ascii % len(salts)
        salt = salts[salt_index]

        token = signing.dumps(payload, salt=salt)
        token = f'{token}:{salt_index}'
        return token

    def format_rupiah(self, price):
        price_int = int(price)
        price_str = str(price_int)
        if len(price_str) <= 3 :
            return 'Rp ' + price_str     
        else :
            p = price_str[-3:]
            q = price_str[:-3]
            return self.format_rupiah(q) + '.' + p


common_service = CommonService()

