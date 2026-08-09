from django.apps import AppConfig


class ShippingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shipping"
    label = "shipping"
    verbose_name = "الشحن والتركيب"

    def ready(self):
        # Registers the commercial-configuration checks (T-2006). Importing here
        # rather than at module scope keeps the app loadable before the registry
        # is populated.
        from . import checks  # noqa: F401
