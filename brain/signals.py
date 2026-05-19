# brain/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Analysis
from integrations.services import send_analysis_to_external_system

@receiver(post_save, sender=Analysis)
def trigger_external_callback(sender, instance, created, **kwargs):
    '''
    Task 8.3.3: Automatically triggers the outbound webhook 
    when the AI analysis status is set to 'done'.
    '''
    # Só enviamos se o status for 'done' e se houver uma URL configurada
    if instance.rag_status == 'done' and instance.job.callback_url:
        # Chamamos o serviço de envio
        send_analysis_to_external_system(instance.id)