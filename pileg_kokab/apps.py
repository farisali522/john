from re import VERBOSE
from django.apps import AppConfig


class PilegKokabConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pileg_kokab'
    verbose_name = 'Pileg Kota/Kabupaten'
