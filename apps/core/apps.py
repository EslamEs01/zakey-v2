from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
    verbose_name = "الإعدادات العامة"

    def ready(self) -> None:
        # Swap in the dashboard-aware admin site once the app registry is
        # populated, so importing models from dashboard.py is safe (T-1308).
        from apps.core.admin_site import install

        install()
