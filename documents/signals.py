import os
import logging
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Document
from brain.vector_store import delete_document_chunks

# Configure logger for traceability
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Document)
def notify_recruiter_on_new_application(sender, instance, created, **kwargs):
    '''
    Task: Dispara um e-mail para o recrutador sempre que um novo 
    candidato se inscreve ou um documento é enviado.
    '''
    if created:
        job = instance.job
        recruiter = job.user
        
        subject = f'[Crivopy] Novo Candidato: {instance.candidate_name}'
        
        message = f'''
        Olá, {recruiter.first_name}!

        Um novo currículo foi recebido para a sua vaga: {job.title}.

        Detalhes do Candidato:
        - Nome: {instance.candidate_name}
        - E-mail: {instance.candidate_email if instance.candidate_email else 'Não informado'}

        O arquivo já está disponível no seu painel. Acesse agora para realizar a análise de IA:
        {settings.SITE_URL}/vagas/{job.id}/documentos/

        Atenciosamente,
        Equipe Crivopy
        '''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recruiter.email],
                fail_silently=True,
            )
            logger.info(f'Notification email sent to {recruiter.email} for new candidate.')
        except Exception as e:
            logger.error(f'Failed to send notification email: {e}')

@receiver(post_delete, sender=Document)
def handle_document_cleanup(sender, instance, **kwargs):
    '''
    Task 5B.7.1: Signal to clean up physical files and vector chunks 
    whenever a Document is deleted.
    '''
    
    # 1. Physical File Cleanup (Maintain logic from Task 4.2)
    if instance.file:
        if os.path.isfile(instance.file.path):
            try:
                os.remove(instance.file.path)
                logger.info(f'Physical file removed: {instance.file.path}')
            except Exception as e:
                logger.error(f'Failed to delete file {instance.file.path}: {e}')

    # 2. Vector Store Cleanup (Task 5B.7.1 implementation)
    try:
        # We call the service that interacts with ChromaDB
        delete_document_chunks(document_id=instance.id)
        logger.info(f'Vector chunks removed from ChromaDB for Document ID: {instance.id}')
    except Exception as e:
        # We log the error but allow the DB transaction to complete
        logger.error(f'Failed to delete vector chunks for Document {instance.id}: {e}')