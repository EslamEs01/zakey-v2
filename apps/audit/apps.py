from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    label = "audit"
    verbose_name = "سجل التدقيق"

    def ready(self) -> None:
        # Importing connects the receivers (T-1406, T-1407).
        from apps.audit import signals  # noqa: F401
