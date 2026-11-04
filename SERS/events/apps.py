from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"
    verbose_name = "SERS"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "SERS Administration"
        admin.site.site_title = "SERS Admin"
        admin.site.index_title = "Administration portal"
        admin.site.index_template = "admin/index.html"
