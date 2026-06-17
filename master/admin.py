from django import forms
from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import XLSX
from .models import Kokab, Kecamatan, Partai
from .resources import KokabResource, KecamatanResource, PartaiResource

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

class PartaiForm(forms.ModelForm):
    class Meta:
        model = Partai
        fields = '__all__'
        widgets = {
            'warna': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px; width: 100px; padding: 0; cursor: pointer;'}),
        }

@admin.register(Partai)
class PartaiAdmin(ImportExportModelAdmin):
    form = PartaiForm
    resource_classes = [PartaiResource]
    formats = [XLSX]
    list_display = ('partai_info', 'warna_preview', 'is_lolos_pt')
    list_editable = ('is_lolos_pt',)
    search_fields = ('nama',)
    ordering = ('no_urut',)
    list_per_page = 20

    @admin.display(description='Partai', ordering='no_urut')
    def partai_info(self, obj):
        if obj.logo_url:
            img_html = format_html(
                '<div style="width: 70px; height: 45px; display: flex; justify-content: center; align-items: center; margin-right: 15px; flex-shrink: 0;">'
                '<img src="{}" style="max-height: 100%; max-width: 100%; object-fit: contain;" />'
                '</div>',
                obj.logo_url
            )
        else:
            img_html = format_html('<div style="width: 70px; height: 45px; margin-right: 15px; flex-shrink: 0;"></div>')
            
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '{}'
            '<div>'
            '<strong style="font-size: 15px; color: #333; line-height: 1.2;">{}</strong><br>'
            '<span style="color: #777; font-size: 13px;">No. Urut: {}</span>'
            '</div>'
            '</div>',
            img_html,
            obj.nama,
            obj.no_urut
        )

    @admin.display(description='Warna')
    def warna_preview(self, obj):
        if obj.warna:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 5px; border: 1px solid #ccc;"></div>',
                obj.warna
            )
        return "-"

    def has_add_permission(self, request):
        return False

    def has_import_permission(self, request):
        return True

    def has_export_permission(self, request):
        return True

