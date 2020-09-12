"""Config service."""
from bolu.models import Config


class ConfigService:
    """ConfigService."""

    def get(self, key, default_value=None):
        """Get config."""
        config = Config.objects.filter(key=key).first()

        if config:
            return config.value
        else:
            return default_value

    def set(self, key, value, description=''):
        """Set config.

        Create if not exists
        otherwise update
        """
        config = self.get(key)

        if not config:
            config = Config.objects.create(key=key, value=value, description=description)
        else:
            config.value = value

            if description:
                config.description = description

            config.save()

        return config

    def set_if_none(self, key, value, description=''):
        """Add config only if not exist."""
        config = self.get(key)

        if not config:
            config = Config.objects.create(key=key, value=value, description=description)

        return config


config_service = ConfigService()
