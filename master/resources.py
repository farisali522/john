from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from .models import Kokab, Kecamatan, Partai

class KokabResource(resources.ModelResource):
    class Meta:
        model = Kokab
        fields = ('kode', 'nama')
        exclude = ('id',)
        import_id_fields = ('kode',)

class KecamatanResource(resources.ModelResource):
    kokab = fields.Field(
        column_name='kabupaten',
        attribute='kokab',
        widget=ForeignKeyWidget(Kokab, field='nama')
    )

    class Meta:
        model = Kecamatan
        fields = ('kode', 'nama', 'kokab', 'jumlah_penduduk', 'dpt_pemilu', 'dpt_pilkada')
        exclude = ('id',)
        import_id_fields = ('kode',)

class PartaiResource(resources.ModelResource):
    class Meta:
        model = Partai
        fields = ('no_urut', 'nama', 'warna', 'logo_url')
        exclude = ('id',)
        import_id_fields = ('no_urut',)
