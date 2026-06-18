from django.db import models

class AksesSimulasi(models.Model):
    class Meta:
        managed = False
        verbose_name = 'Dashboard Simulasi'
        verbose_name_plural = 'Dashboard Simulasi'
        default_permissions = ()
        permissions = [
            ("can_access_simulasi", "Dapat Mengakses Simulasi Rebut Kursi"),
        ]
