from django.db import models
from master.models import Kokab, Kecamatan, Partai

class Dapil(models.Model):
    kokab = models.ForeignKey(Kokab, on_delete=models.CASCADE, related_name='dapil_kokab_set')
    kecamatan = models.ManyToManyField(Kecamatan, related_name='dapil_kokab_set')
    nama = models.CharField(max_length=255, unique=True)
    jumlah_kursi = models.IntegerField()

    def __str__(self):
        return f"{self.nama}"

    class Meta:
        verbose_name = 'Dapil'
        verbose_name_plural = 'Dapil'

class RekapSuara(models.Model):
    kecamatan = models.OneToOneField(Kecamatan, on_delete=models.CASCADE, related_name='rekap_suara_kokab')
    suara_tidak_sah = models.IntegerField(default=0)

    def __str__(self):
        return f"Rekap: {self.kecamatan.nama}"

    class Meta:
        verbose_name = 'Rekap Suara'
        verbose_name_plural = 'Rekap Suara'


class DetailSuara(models.Model):
    rekap_suara = models.ForeignKey(RekapSuara, on_delete=models.CASCADE, related_name='detail_suara')
    partai = models.ForeignKey(Partai, on_delete=models.CASCADE, related_name='detail_suara_kokab_set')
    jumlah_suara = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.partai.nama} - {self.jumlah_suara}"

    class Meta:
        unique_together = ('rekap_suara', 'partai')

class RekapKursiKokab(Kokab):
    class Meta:
        proxy = True
        verbose_name = 'Rekap Kursi per Kota/Kab'
        verbose_name_plural = 'Rekap Kursi per Kota/Kab'
