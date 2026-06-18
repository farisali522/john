from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import RiwayatLogin

@receiver(user_logged_in)
def rekam_ip_login(sender, request, user, **kwargs):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    
    RiwayatLogin.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent
    )
