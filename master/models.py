from django.db import models

class Kokab(models.Model):
    kode = models.CharField(max_length=24, unique=True)
    nama = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = 'Kota/Kabupaten'
        verbose_name_plural = 'Kota/Kabupaten'

    def __str__(self):
        return f"{self.nama}"

class Kecamatan(models.Model):
    kokab = models.ForeignKey(Kokab, on_delete=models.CASCADE)
    kode = models.CharField(max_length=24, unique=True)
    nama = models.CharField(max_length=255)
    jumlah_penduduk = models.IntegerField()
    dpt_pemilu = models.IntegerField()
    dpt_pilkada = models.IntegerField()

    class Meta:
        verbose_name = 'Kecamatan'
        verbose_name_plural = 'Kecamatan'
        unique_together = ('kokab', 'nama')

    def __str__(self):
        return f"{self.kokab} | {self.kode} | {self.nama}"