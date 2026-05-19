# views.py
import json
from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from hub.models import Job
from documents.models import Document
from .models import IntegrationLog
from .services import download_resume_from_url, verify_and_sync_single_job

@method_decorator(csrf_exempt, name='dispatch') # Webhooks externos não usam CSRF token
class SolidesWebhookView(View):
    '''
    Task 8.2.1: Endpoint to receive candidate data from Sólides.
    '''
    
    def post(self, request, *args, **kwargs):
        # Validação do Token no Header (Segurança)
        token = request.headers.get('X-Crivopy-Token')
        if token != settings.SOLIDES_INTEGRATION_TOKEN:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        try:
            payload = json.loads(request.body)
            
            external_job_id = payload.get('vaga_id')
            candidate_name = payload.get('nome')
            candidate_email = payload.get('email')
            resume_url = payload.get('curriculo_url')

            # Task 8.2.2: Busca a vaga pelo external_id no Crivopy
            job = Job.objects.filter(external_id=external_job_id, external_source='solides').first()
            
            # AUTOMAÇÃO INTELIGENTE: Se a vaga não existe localmente, fazemos a checagem ativa se ela é elegível (ativa)
            if not job:
                job = verify_and_sync_single_job(external_job_id)
                
            # Se mesmo após a checagem o objeto 'job' não retornar ou estiver com status inativo, rejeitamos
            if not job or job.status != 'ACTIVE':
                self._log_integration(None, payload, 422, False, f'Inbound negado: Vaga {external_job_id} está inativa, cancelada ou não foi encontrada na Sólides.')
                return JsonResponse({'error': 'Vaga inativa ou inexistente na Sólides. Processamento ignorado.'}, status=422)

            # Task 8.2.3: Processa o download do arquivo
            resume_file = download_resume_from_url(resume_url, candidate_name)

            # Task 8.2.4: Cria o Documento com status inicial 'pending'
            document = Document.objects.create(
                job=job,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                file=resume_file,
                status='pending' # Padrão conforme PRD
            )

            self._log_integration(job, payload, 201, True)
            return JsonResponse({'status': 'success', 'document_id': document.id}, status=201)

        except Exception as e:
            self._log_integration(None, request.body, 500, False, str(e))
            return JsonResponse({'error': str(e)}, status=500)

    def _log_integration(self, job, payload, status_code, success, error_message=''):
        '''Grava o histórico na tabela de auditoria da Tarefa 8.1.3'''
        IntegrationLog.objects.create(
            job=job,
            external_source='solides',
            direction='INBOUND',
            payload=payload,
            status_code=status_code,
            success=success,
            error_message=error_message
        )