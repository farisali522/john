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

class Partai(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    no_urut = models.IntegerField(unique=True)
    warna = models.CharField(max_length=50, default='#808080', help_text='Kode Hex (contoh: #808080)')
    logo_url = models.URLField(max_length=200, blank=True, null=True)
    is_lolos_pt = models.BooleanField(default=False, verbose_name="Lolos PT 4%", help_text="Centang jika partai ini lolos Ambang Batas Parlemen (Khusus DPR RI)")

    def __str__(self):
        return f"{self.nama}"

    class Meta:
        verbose_name_plural = "Partai"

from django.contrib.auth.models import User

class RiwayatLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Pengguna")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.CharField(max_length=255, null=True, blank=True, verbose_name="Browser/Perangkat")
    waktu_login = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Login")

    class Meta:
        verbose_name = 'Riwayat Login'
        verbose_name_plural = 'Riwayat Login'
        ordering = ['-waktu_login']

    def __str__(self):
        return f"{self.user.username} - {self.waktu_login.strftime('%Y-%m-%d %H:%M:%S')}"