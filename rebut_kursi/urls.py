from django.urls import path
from . import views

app_name = 'rebut_kursi'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/simulate/', views.simulate_view, name='simulate'),
]
