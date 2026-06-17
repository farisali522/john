from import_export import fields, resources
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget
from master.models import Kokab, Kecamatan, Partai
from .models import Dapil, RekapSuara, DetailSuara

# Membuat Widget Khusus agar tahan terhadap spasi (contoh: "Kota Bandung, Kota Cimahi")
class KokabManyToManyWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return self.model.objects.none()
        # Memisahkan berdasarkan koma dan membuang spasi kosong di sekitarnya
        names = [n.strip() for n in value.split(',')]
        return self.model.objects.filter(nama__in=names)

class DapilResource(resources.ModelResource):
    # Kolom kustom untuk ManyToMany Kokab
    kokab = fields.Field(
        column_name='cakupan_wilayah', # Nama kolom di file Excel
        attribute='kokab',
        widget=KokabManyToManyWidget(Kokab, field='nama', separator=', ')
    )

    class Meta:
        model = Dapil
        # Urutan kolom di Excel
        fields = ('nama', 'jumlah_kursi', 'kokab')
        import_id_fields = ('nama',) # Menggunakan nama sebagai sidik jari (karena unik)
        export_order = ('nama', 'jumlah_kursi', 'kokab')

class RekapSuaraResource(resources.ModelResource):
    kecamatan = fields.Field(
        column_name='kode_kecamatan',
        attribute='kecamatan',
        widget=ForeignKeyWidget(Kecamatan, field='kode')
    )
    nama_kecamatan = fields.Field(
        column_name='nama_kecamatan',
        attribute='kecamatan__nama',
        readonly=True # Hanya diisi saat export, tidak dibaca saat import
    )
    suara_tidak_sah = fields.Field(
        column_name='suara_tidak_sah',
        attribute='suara_tidak_sah'
    )

    class Meta:
        model = RekapSuara
        fields = ('kecamatan', 'nama_kecamatan', 'suara_tidak_sah')
        import_id_fields = ('kecamatan',)
        export_order = ('kecamatan', 'nama_kecamatan', 'suara_tidak_sah')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. Ambil daftar partai dan urutkan sesuai no urut
        self.partai_list = list(Partai.objects.all().order_by('no_urut'))
        
        # 2. Sisipkan kolom-kolom partai secara dinamis
        for partai in self.partai_list:
            field_name = partai.nama.lower()
            self.fields[field_name] = fields.Field(
                column_name=partai.nama.lower(),
                attribute=f'dummy_{partai.id}', # Dummy attribute
                readonly=False # HARUS False agar nilai dari Excel dibaca ke memori object saat preview!
            )
            # Urutkan di Excel agar partai muncul paling kanan
            self.Meta.export_order = self.Meta.export_order + (field_name,)

    def export_field(self, field, obj):
        # Saat EXPORT atau PREVIEW:
        if field.column_name in [p.nama.lower() for p in self.partai_list]:
            # Jika ini dari proses Import/Preview, ambil nilainya dari memori object
            if hasattr(obj, field.attribute):
                return getattr(obj, field.attribute)
            
            # Jika ini dari proses Export murni (dari Database), tarik dari tabel DetailSuara
            if not obj.pk:
                return 0 # Jangan query jika object belum disave (mencegah ValueError)
            
            detail = obj.detail_suara.filter(partai__nama__iexact=field.column_name).first()
            return detail.jumlah_suara if detail else 0
        return super().export_field(field, obj)

    def after_save_instance(self, instance, row, **kwargs):
        # Saat IMPORT (setelah save Rekap): Simpan/update data DetailSuara
        # super() tidak dipanggil karena API bawaan tidak menerima kwargs
        
        dry_run = kwargs.get('dry_run', False)
        if not dry_run and row:
            data = row
            for partai in self.partai_list:
                # Cek apakah header nama partai ini ada di file Excel
                nama_kolom = partai.nama.lower()
                if nama_kolom in data:
                    suara = data[nama_kolom]
                    # Pastikan formatnya angka, jika kosong jadikan 0
                    try:
                        suara = int(suara)
                    except (ValueError, TypeError):
                        suara = 0
                    
                    # Hubungkan Suara Partai ke Rekap Kecamatan ini
                    DetailSuara.objects.update_or_create(
                        rekap_suara=instance,
                        partai=partai,
                        defaults={'jumlah_suara': suara}
                    )
