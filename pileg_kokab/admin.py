from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats

from master.models import Partai

from .models import Dapil, RekapSuara, DetailSuara, RekapKursiKokab
from .resources import DapilResource, RekapSuaraResource


def format_angka(value):
    if value is None:
        return '0'
    return f"{value:,}".replace(',', '.')


class DapilForm(forms.ModelForm):
    class Meta:
        model = Dapil
        fields = '__all__'


@admin.register(Dapil)
class DapilAdmin(ImportExportModelAdmin):
    form = DapilForm
    resource_classes = [DapilResource]
    formats = [base_formats.XLSX]
    # list_display dibuat dinamis via get_list_display
    search_fields = ('nama', 'kokab__nama')
    list_filter = ('kokab',)
    filter_horizontal = ('kecamatan',)
    ordering = ('id',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('kokab').prefetch_related('kecamatan__rekap_suara_kokab__detail_suara')

    @admin.display(description='Kabupaten/Kota', ordering='kokab__nama')
    def get_kokab(self, obj):
        return obj.kokab.nama

    def get_suara_partai_dict(self, dapil_obj):
        if hasattr(dapil_obj, '_suara_partai_dict'):
            return dapil_obj._suara_partai_dict

        partai_dict = {p.id: 0 for p in Partai.objects.all()}

        for kec in dapil_obj.kecamatan.all():
            if hasattr(kec, 'rekap_suara_kokab'):
                for detail in kec.rekap_suara_kokab.detail_suara.all():
                    if detail.partai_id in partai_dict:
                        partai_dict[detail.partai_id] += detail.jumlah_suara
        
        dapil_obj._suara_partai_dict = partai_dict
        return partai_dict

    def get_kursi_partai_dict(self, dapil_obj):
        if hasattr(dapil_obj, '_kursi_partai_dict'):
            return dapil_obj._kursi_partai_dict

        suara_dict = self.get_suara_partai_dict(dapil_obj)
        from master.sainte_lague import hitung_sainte_lague
        kursi_dict = hitung_sainte_lague(dapil_obj.jumlah_kursi, suara_dict)
        
        dapil_obj._kursi_partai_dict = kursi_dict
        return kursi_dict

    def get_global_kursi_partai(self):
        if hasattr(self, '_global_kursi_partai'):
            return self._global_kursi_partai

        from master.sainte_lague import hitung_sainte_lague
        global_kursi = {}
        for dapil in Dapil.objects.select_related('kokab').prefetch_related('kecamatan__rekap_suara_kokab__detail_suara'):
            suara_dict = self.get_suara_partai_dict(dapil)
            kursi_dict = hitung_sainte_lague(dapil.jumlah_kursi, suara_dict)
            for pid, kursi in kursi_dict.items():
                global_kursi[pid] = global_kursi.get(pid, 0) + kursi
        
        self._global_kursi_partai = global_kursi
        return global_kursi

    def get_list_display(self, request):
        list_display = ['nama', 'jumlah_kursi', 'get_kokab']
        
        # Hapus cache setiap kali load halaman agar data selalu fresh
        if hasattr(self, '_global_kursi_partai'):
            delattr(self, '_global_kursi_partai')
        
        for partai in Partai.objects.order_by('no_urut'):
            method_name = f'info_kursi_partai_{partai.pk}'
            # Simpan method ke instance (self), bukan ke class agar dinamis per request
            method = self.make_kursi_partai_method(partai)
            setattr(self, method_name, method)
            list_display.append(method_name)
            
        return tuple(list_display)

    def get_partai_header(self, partai):
        global_kursi = self.get_global_kursi_partai()
        total_kursi = global_kursi.get(partai.id, 0)

        logo_html = format_html(
            '<span style="display:inline-flex;align-items:center;'
            'justify-content:center;width:28px;height:28px;border-radius:4px;'
            'background:#f3f4f6;border:1px solid #d1d5db;color:#9ca3af;'
            'font-size:12px;">{}</span>',
            partai.no_urut
        )

        if partai.logo_url:
            logo_html = format_html(
                '<img src="{}" alt="{}" style="width:28px;height:28px;'
                'object-fit:contain;border-radius:4px;border:1px solid #d1d5db;">',
                partai.logo_url,
                partai.nama
            )

        return format_html(
            '<span style="display:inline-flex;flex-direction:column;'
            'align-items:center;gap:2px;min-width:52px;line-height:1.1;">'
            '{}<strong>#{}</strong><small style="font-weight:400;">{}</small>'
            '<span style="color:#059669; font-weight:bold; font-size:12px; margin-top:2px; padding:0 4px; background:#dcfce7; border-radius:4px;">{} Kursi</span>'
            '</span>',
            logo_html,
            partai.no_urut,
            partai.nama,
            total_kursi
        )

    def make_kursi_partai_method(self, partai):
        def kursi_partai(obj):
            kursi_dict = self.get_kursi_partai_dict(obj)
            jumlah_kursi = kursi_dict.get(partai.id, 0)
            
            if jumlah_kursi > 0:
                hex_color = str(partai.warna).strip() if partai.warna else '#cccccc'
                bg_color = hex_color
                if bg_color.startswith('#') and len(bg_color) == 7:
                    bg_color = bg_color + '33'
                elif bg_color.startswith('#') and len(bg_color) == 4:
                    bg_color = f"#{bg_color[1]*2}{bg_color[2]*2}{bg_color[3]*2}33"

                return format_html(
                    '<div style="text-align:center;"><div style="background-color:{}; color:#212529; padding:4px 8px; border-radius:6px; display:inline-block; border:1px solid {}; font-weight:bold; font-size:14px;">{}</div></div>',
                    bg_color,
                    hex_color,
                    jumlah_kursi
                )
            else:
                return format_html('<div style="text-align:center; color:#ccc;">-</div>')

        kursi_partai.short_description = self.get_partai_header(partai)
        kursi_partai.__name__ = f'info_kursi_partai_{partai.pk}'
        return kursi_partai


class PartaiSuaraInput(forms.NumberInput):
    def __init__(self, partai, attrs=None):
        super().__init__(attrs)
        self.partai = partai

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        logo_html = format_html(
            '<span class="img-thumbnail d-inline-flex align-items-center '
            'justify-content-center mr-3" style="width:42px;height:42px;'
            'color:#6c757d;">{}</span>',
            self.partai.no_urut
        )

        if self.partai.logo_url:
            logo_html = format_html(
                '<img src="{}" alt="{}" class="img-thumbnail mr-3" '
                'style="width:42px;height:42px;object-fit:contain;">',
                self.partai.logo_url,
                self.partai.nama
            )

        return format_html(
            '<div class="d-flex align-items-center" style="max-width:590px;">{}'
            '<div class="mr-3" style="min-width:210px;">'
            '<strong>PARTAI #{}</strong><br>'
            '<span>{}</span></div>'
            '<div style="width:180px;">{}</div></div>',
            logo_html,
            self.partai.no_urut,
            self.partai.nama,
            input_html
        )


class RekapSuaraAdminForm(forms.ModelForm):
    class Meta:
        model = RekapSuara
        fields = ('kecamatan', 'suara_tidak_sah')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.partai_list = list(Partai.objects.order_by('no_urut'))

        for partai in self.partai_list:
            field_name = self.get_partai_field_name(partai)
            initial = 0

            if self.instance and self.instance.pk:
                detail = self.instance.detail_suara.filter(
                    partai=partai
                ).first()
                if detail:
                    initial = detail.jumlah_suara

            self.fields[field_name] = self.make_partai_suara_field(
                partai,
                initial=initial
            )
            self.initial[field_name] = initial

    @classmethod
    def make_partai_suara_field(cls, partai, initial=0):
        return forms.IntegerField(
            min_value=0,
            required=False,
            initial=initial,
            label=f'Suara Partai #{partai.no_urut}',
            widget=PartaiSuaraInput(
                partai,
                attrs={
                    'class': 'form-control text-right suara-partai-input',
                    'style': 'width:100%; font-weight:bold;'
                }
            )
        )

    @staticmethod
    def get_partai_field_name(partai):
        return f'suara_partai_{partai.pk}'

    def save_detail_suara(self, instance):
        for partai in self.partai_list:
            field_name = self.get_partai_field_name(partai)
            jumlah_suara = self.cleaned_data.get(field_name) or 0

            DetailSuara.objects.update_or_create(
                rekap_suara=instance,
                partai=partai,
                defaults={'jumlah_suara': jumlah_suara}
            )


@admin.register(RekapSuara)
class RekapSuaraAdmin(ImportExportModelAdmin):
    form = RekapSuaraAdminForm
    resource_classes = [RekapSuaraResource]
    readonly_fields = ('info_suara_sah_form', 'info_total_suara_form')
    list_filter = ('kecamatan__kokab',)
    search_fields = (
        'kecamatan__kode',
        'kecamatan__nama',
        'kecamatan__kokab__nama',
    )
    ordering = ('kecamatan__kode',)
    list_per_page = 15
    list_max_show_all = 700

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('kecamatan', 'kecamatan__kokab').prefetch_related('detail_suara')

    def get_partai_form_fields(self):
        return [
            RekapSuaraAdminForm.get_partai_field_name(partai)
            for partai in Partai.objects.order_by('no_urut')
        ]

    def get_fields(self, request, obj=None):
        return [
            'kecamatan',
            'suara_tidak_sah',
            *self.get_partai_form_fields(),
            'info_suara_sah_form',
            'info_total_suara_form',
        ]

    def get_form(self, request, obj=None, **kwargs):
        dynamic_fields = {}

        for partai in Partai.objects.order_by('no_urut'):
            field_name = RekapSuaraAdminForm.get_partai_field_name(partai)
            dynamic_fields[field_name] = (
                RekapSuaraAdminForm.make_partai_suara_field(partai)
            )

        kwargs['form'] = type(
            'RekapSuaraAdminDynamicForm',
            (self.form,),
            dynamic_fields
        )
        return super().get_form(request, obj, **kwargs)

    def get_list_display(self, request):
        list_display = ['wilayah', 'info_dpt']

        for partai in Partai.objects.order_by('no_urut'):
            method_name = f'info_suara_partai_{partai.pk}'
            if not hasattr(self.__class__, method_name):
                setattr(self.__class__, method_name, self.make_suara_partai_method(partai))
            list_display.append(method_name)

        list_display.extend([
            'info_suara_sah',
            'info_suara_tidak_sah',
            'info_total_suara',
        ])
        return tuple(list_display)

    def get_partai_header(self, partai):
        logo_html = format_html(
            '<span style="display:inline-flex;align-items:center;'
            'justify-content:center;width:28px;height:28px;border-radius:4px;'
            'background:#f3f4f6;border:1px solid #d1d5db;color:#9ca3af;'
            'font-size:12px;">{}</span>',
            partai.no_urut
        )

        if partai.logo_url:
            logo_html = format_html(
                '<img src="{}" alt="{}" style="width:28px;height:28px;'
                'object-fit:contain;border-radius:4px;border:1px solid #d1d5db;">',
                partai.logo_url,
                partai.nama
            )

        return format_html(
            '<span style="display:inline-flex;flex-direction:column;'
            'align-items:center;gap:2px;min-width:52px;line-height:1.1;">'
            '{}<strong>#{}</strong><small style="font-weight:400;">{}</small>'
            '</span>',
            logo_html,
            partai.no_urut,
            partai.nama
        )

    def make_suara_partai_method(self, partai):
        def suara_partai(self, obj):
            if not hasattr(obj, '_max_suara'):
                all_suara = [d.jumlah_suara for d in obj.detail_suara.all()]
                obj._max_suara = max(all_suara) if all_suara else 0

            suara_sah = self.get_suara_sah(obj)
            jumlah_suara = self.get_jumlah_suara_partai(obj, partai)
            persen = self.get_persen(jumlah_suara, suara_sah)

            is_highest = (jumlah_suara == obj._max_suara) and (jumlah_suara > 0)
            hex_color = str(partai.warna).strip() if partai.warna else '#cccccc'
            
            bg_color = hex_color
            if bg_color.startswith('#') and len(bg_color) == 7:
                bg_color = bg_color + '33'
            elif bg_color.startswith('#') and len(bg_color) == 4:
                bg_color = f"#{bg_color[1]*2}{bg_color[2]*2}{bg_color[3]*2}33"

            if is_highest:
                return format_html(
                    '<div style="text-align:center;"><div style="background-color:{}; color:#212529; padding:4px 8px; border-radius:6px; display:inline-block; border:1px solid {};"><strong>{}</strong><br><small style="color:#6c757d;">({}%)</small></div></div>',
                    bg_color,
                    hex_color,
                    format_angka(jumlah_suara),
                    self.format_persen(persen)
                )
            else:
                return format_html(
                    '<div style="text-align:center; color:#212529; padding:5px;"><strong>{}</strong><br><small style="color:#6c757d;">({}%)</small></div>',
                    format_angka(jumlah_suara),
                    self.format_persen(persen)
                )
            
        suara_partai.short_description = self.get_partai_header(partai)
        suara_partai.__name__ = f'info_suara_partai_{partai.pk}'
        return suara_partai

    def get_jumlah_suara_partai(self, obj, partai):
        for detail in obj.detail_suara.all():
            if detail.partai_id == partai.pk:
                return detail.jumlah_suara
        return 0

    def get_suara_sah(self, obj):
        return sum(detail.jumlah_suara for detail in obj.detail_suara.all())

    def get_total_suara(self, obj):
        return self.get_suara_sah(obj) + obj.suara_tidak_sah

    def get_persen(self, value, total):
        if not total:
            return 0
        return (value / total) * 100

    def format_persen(self, value):
        return f'{value:.2f}'

    @admin.display(description='Suara Sah')
    def info_suara_sah_form(self, obj):
        if not obj or not obj.pk:
            return format_html('<span id="rekap-suara-sah">0</span>')
        return format_html(
            '<span id="rekap-suara-sah">{}</span>',
            format_angka(self.get_suara_sah(obj))
        )

    @admin.display(description='Total Suara')
    def info_total_suara_form(self, obj):
        if not obj or not obj.pk:
            return format_html('<span id="rekap-total-suara">0</span>')
        return format_html(
            '<span id="rekap-total-suara">{}</span>',
            format_angka(self.get_total_suara(obj))
        )

    @admin.display(description='Wilayah', ordering='kecamatan__kode')
    def wilayah(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.kecamatan.nama,
            obj.kecamatan.kokab.nama
        )

    @admin.display(description='DPT')
    def info_dpt(self, obj):
        return format_html(
            '<strong>{}</strong>',
            format_angka(obj.kecamatan.dpt_pemilu)
        )

    @admin.display(description='Suara Tidak Sah')
    def info_suara_tidak_sah(self, obj):
        total_suara = self.get_total_suara(obj)
        persen = self.get_persen(obj.suara_tidak_sah, total_suara)

        return format_html(
            '<div style="text-align:center;"><span style="color:#dc2626;">{}</span><br>'
            '<small>({}%)</small></div>',
            format_angka(obj.suara_tidak_sah),
            self.format_persen(persen)
        )

    @admin.display(description='Suara Sah')
    def info_suara_sah(self, obj):
        suara_sah = self.get_suara_sah(obj)
        total_suara = self.get_total_suara(obj)
        persen = self.get_persen(suara_sah, total_suara)

        return format_html(
            '<div style="text-align:center;"><span style="color:#16a34a;">{}</span><br>'
            '<small>({}%)</small></div>',
            format_angka(suara_sah),
            self.format_persen(persen)
        )

    @admin.display(description='Total Suara')
    def info_total_suara(self, obj):
        total_suara = self.get_total_suara(obj)
        dpt = obj.kecamatan.dpt_pemilu
        persen = self.get_persen(total_suara, dpt)

        return format_html(
            '<div style="text-align:center;"><span style="color:#2563eb;">{}</span><br>'
            '<small>({}%)</small></div>',
            format_angka(total_suara),
            self.format_persen(persen)
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        if hasattr(form, 'save_detail_suara'):
            form.save_detail_suara(form.instance)

    def has_add_permission(self, request):
        return False

    def get_import_formats(self):
        return [base_formats.XLSX]

    def get_export_formats(self):
        return [base_formats.XLSX]


@admin.register(RekapKursiKokab)
class RekapKursiKokabAdmin(admin.ModelAdmin):
    list_display = ['nama']
    search_fields = ('nama',)
    ordering = ('kode',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('dapil_kokab_set__kecamatan__rekap_suara_kokab__detail_suara')

    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

    def get_list_display(self, request):
        list_display = ['nama']
        
        for partai in Partai.objects.order_by('no_urut'):
            method_name = f'info_total_kursi_partai_{partai.pk}'
            method = self.make_total_kursi_partai_method(partai)
            setattr(self, method_name, method)
            list_display.append(method_name)
            
        return tuple(list_display)

    def get_partai_header(self, partai):
        logo_html = format_html(
            '<span style="display:inline-flex;align-items:center;'
            'justify-content:center;width:28px;height:28px;border-radius:4px;'
            'background:#f3f4f6;border:1px solid #d1d5db;color:#9ca3af;'
            'font-size:12px;">{}</span>',
            partai.no_urut
        )

        if partai.logo_url:
            logo_html = format_html(
                '<img src="{}" alt="{}" style="width:28px;height:28px;'
                'object-fit:contain;border-radius:4px;border:1px solid #d1d5db;">',
                partai.logo_url,
                partai.nama
            )

        return format_html(
            '<span style="display:inline-flex;flex-direction:column;'
            'align-items:center;gap:2px;min-width:52px;line-height:1.1;">'
            '{}<strong>#{}</strong><small style="font-weight:400;">{}</small>'
            '</span>',
            logo_html,
            partai.no_urut,
            partai.nama
        )

    def get_total_kursi_kokab(self, obj):
        if hasattr(obj, '_total_kursi_dict'):
            return obj._total_kursi_dict
        
        total_kursi_dict = {p.id: 0 for p in Partai.objects.all()}
        from master.sainte_lague import hitung_sainte_lague
        
        for dapil in obj.dapil_kokab_set.all():
            partai_dict = {p.id: 0 for p in Partai.objects.all()}
            for kec in dapil.kecamatan.all():
                if hasattr(kec, 'rekap_suara_kokab'):
                    for detail in kec.rekap_suara_kokab.detail_suara.all():
                        if detail.partai_id in partai_dict:
                            partai_dict[detail.partai_id] += detail.jumlah_suara
            
            kursi_dict = hitung_sainte_lague(dapil.jumlah_kursi, partai_dict)
            for pid, kursi in kursi_dict.items():
                total_kursi_dict[pid] += kursi
        
        obj._total_kursi_dict = total_kursi_dict
        return total_kursi_dict

    def make_total_kursi_partai_method(self, partai):
        def total_kursi_partai(obj):
            kursi_dict = self.get_total_kursi_kokab(obj)
            total = kursi_dict.get(partai.id, 0)
            
            if total > 0:
                hex_color = str(partai.warna).strip() if partai.warna else '#cccccc'
                bg_color = hex_color
                if bg_color.startswith('#') and len(bg_color) == 7:
                    bg_color = bg_color + '33'
                elif bg_color.startswith('#') and len(bg_color) == 4:
                    bg_color = f"#{bg_color[1]*2}{bg_color[2]*2}{bg_color[3]*2}33"

                return format_html(
                    '<div style="text-align:center;"><div style="background-color:{}; color:#212529; padding:4px 8px; border-radius:6px; display:inline-block; border:1px solid {}; font-weight:bold; font-size:14px;">{}</div></div>',
                    bg_color,
                    hex_color,
                    total
                )
            else:
                return format_html('<div style="text-align:center; color:#ccc;">-</div>')

        total_kursi_partai.short_description = self.get_partai_header(partai)
        total_kursi_partai.__name__ = f'info_total_kursi_partai_{partai.pk}'
        return total_kursi_partai
