from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        # import signal handlers so they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            # avoid breaking startup if imports raise errors during migrations
            pass
