from django.db import models
from hub.models import Job  # Certifique-se de que o caminho para o modelo Job está correto

class IntegrationLog(models.Model):
    """
    Registra o histórico de requisições dos Webhooks externos (Sólides, etc).
    Essencial para auditoria, debug de erros e monitoramento de payloads.
    """
    # Vinculação opcional com a vaga correspondente (caso exista)
    job = models.ForeignKey(
        Job, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Vaga associada à integração, se aplicável'
    )
    
    # Substitui ou mapeia o antigo 'provider'
    external_source = models.CharField(
        max_length=100, 
        default='solides',
        help_text='Nome do provedor externo (ex: solides)'
    )
    
    # Identifica o fluxo do dado
    direction = models.CharField(
        max_length=20,
        default='INBOUND',
        help_text='Direção do fluxo: INBOUND (recebido) ou OUTBOUND (enviado)'
    )
    
    # Guarda o payload em formato JSON estruturado (ou TextField se preferir)
    payload = models.JSONField(
        blank=True, 
        null=True, 
        help_text='JSON bruto da requisição/resposta'
    )
    
    status_code = models.IntegerField(
        blank=True, 
        null=True, 
        help_text='Status HTTP retornado pelo Crivopy'
    )
    
    # Flag para saber rapidamente se correu tudo bem
    success = models.BooleanField(
        default=True,
        help_text='Indica se a integração ocorreu com sucesso'
    )
    
    # Guarda a mensagem de sucesso ou o rasto do erro (traceback/exception)
    error_message = models.TextField(
        blank=True, 
        null=True, 
        help_text='Mensagem descritiva de sucesso ou erro'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Data e hora em que o log foi gerado'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log de Integração'
        verbose_name_plural = 'Logs de Integrações'

    def __str__(self):
        status = "Sucesso" if self.success else "Falha"
        return f"{self.external_source.upper()} [{self.direction}] ({self.status_code}) - {status}"