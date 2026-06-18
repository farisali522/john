from django.apps import AppConfig

class MasterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'master'

    def ready(self):
        from django.apps import apps
        apps.get_app_config('auth').verbose_name = 'Auth'
        import master.signals
