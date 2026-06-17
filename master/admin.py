from django.contrib import admin
from django.db.models import Sum
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import XLSX
from .models import Kokab, Kecamatan
from .resources import KokabResource, KecamatanResource

@admin.register(Kokab)
class KokabAdmin(ImportExportModelAdmin):
    resource_classes = [KokabResource]
    formats = [XLSX]
    list_display = ('nama', 'get_jumlah_penduduk', 'get_dpt_pemilu', 'get_dpt_pilkada')
    search_fields = ('nama',)
    ordering = ('kode',)
    list_per_page = 27

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            total_penduduk=Sum('kecamatan__jumlah_penduduk'),
            total_dpt_pemilu=Sum('kecamatan__dpt_pemilu'),
            total_dpt_pilkada=Sum('kecamatan__dpt_pilkada')
        )

    @admin.display(description='Jumlah Penduduk', ordering='total_penduduk')
    def get_jumlah_penduduk(self, obj):
        return obj.total_penduduk or 0

    @admin.display(description='DPT Pemilu', ordering='total_dpt_pemilu')
    def get_dpt_pemilu(self, obj):
        return obj.total_dpt_pemilu or 0

    @admin.display(description='DPT Pilkada', ordering='total_dpt_pilkada')
    def get_dpt_pilkada(self, obj):
        return obj.total_dpt_pilkada or 0

    def has_add_permission(self, request):
        return False

    def has_import_permission(self, request):
        return False

    def has_export_permission(self, request):
        return False

@admin.register(Kecamatan)
class KecamatanAdmin(ImportExportModelAdmin):
    resource_classes = [KecamatanResource]
    formats = [XLSX]
    list_display = ('nama', 'kokab',  'jumlah_penduduk', 'dpt_pemilu', 'dpt_pilkada')
    search_fields = ('nama', 'kokab__nama')
    list_filter = ('kokab',)
    ordering = ('kode',)
    list_per_page = 20
    list_max_show_all = 700


    def has_add_permission(self, request):
        return False

    def has_import_permission(self, request):
        return False

    def has_export_permission(self, request):
        return False
