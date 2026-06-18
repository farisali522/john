from django.contrib import admin
from django.shortcuts import redirect
from .models import AksesSimulasi

@admin.register(AksesSimulasi)
class AksesSimulasiAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect('rebut_kursi:dashboard')

    def has_module_permission(self, request):
        return request.user.has_perm('rebut_kursi.can_access_simulasi')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('rebut_kursi.can_access_simulasi')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
