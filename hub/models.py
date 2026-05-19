import uuid # Task: Required for UUID generation
from django.db import models
from django.conf import settings

class Job(models.Model):
    '''
    Represents a job position created by a recruiter.
    Central model for managing candidates and documents.
    '''
    
    # Status constants (Portuguese labels for UI)
    ACTIVE = 'ACTIVE'
    PAUSED = 'PAUSED'
    ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (ACTIVE, 'Ativa'),
        (PAUSED, 'Pausada'),
        (ARCHIVED, 'Arquivada'),
    ]

    # Task 3.1.2: FK to User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobs'
    )

    # Task: Public token for unique candidate links
    public_token = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        null=False,
    )

    # Task 3.1.3: Title
    title = models.CharField(max_length=255)

    # Task 3.1.4: Description
    description = models.TextField(blank=True)

    # Task 3.1.5: Status with choices
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )

    # Task 3.1.6: Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- NOVOS CAMPOS PARA INTEGRAÇÃO (ADICIONADOS AQUI) ---

    # Task 8.1.2: External Mapping (Sólides / Outros ATS)
    external_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text='ID desta vaga no sistema externo (ex: ID da Sólides)'
    )
    external_source = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text='Nome do sistema de origem (ex: solides)'
    )

    # Task 8.3.1: URL de destino para resultados
    callback_url = models.URLField(
        blank=True, 
        null=True, 
        help_text='URL do sistema que receberá as notas e resumos da IA'
    )

    # ------------------------------------------------------

    # Task 3.1.8: Meta configuration
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vaga'
        verbose_name_plural = 'Vagas'

    # Task 3.1.7: String representation
    def __str__(self):
        return self.title