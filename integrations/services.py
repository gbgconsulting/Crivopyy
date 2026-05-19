# services.py
import requests
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from hub.models import Job
from users.models import User
from .models import IntegrationLog

logger = logging.getLogger(__name__)

def verify_and_sync_single_job(vaga_id: str):
    """
    Busca os detalhes da vaga na Sólides sob demanda para verificar o status.
    Se a vaga estiver ativa, cria/atualiza no Crivopy e retorna o Job.
    """
    base_url = settings.SOLIDES_API_BASE_URL
    token = settings.SOLIDES_API_TOKEN
    
    endpoint = f"{base_url}/vagas/{vaga_id}/candidatos"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(endpoint, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.warning(f"Vaga {vaga_id} não retornou dados ativos na Sólides (Status {response.status_code}).")
            return None

        recruiter = User.objects.filter(is_superuser=True).first()
        if not recruiter:
            recruiter = User.objects.first()

        job, created = Job.objects.update_or_create(
            external_id=str(vaga_id),
            external_source='solides',
            defaults={
                'user': recruiter,
                'title': f"Vaga Sólides #{vaga_id}",
                'description': "Criada automaticamente sob demanda via Webhook ativo.",
                'status': 'ACTIVE'
            }
        )

        IntegrationLog.objects.create(
            job=job,
            external_source='solides',
            direction='OUTBOUND',
            payload={"vaga_id": vaga_id, "info": "Mapeamento ativo sob demanda"},
            status_code=response.status_code,
            success=True,
            error_message=f"Vaga {vaga_id} verificado e sincronizada como ATIVA."
        )
        return job

    except Exception as e:
        logger.error(f"Erro ao verificar vaga {vaga_id} ativamente na Sólides: {str(e)}")
        return None

def download_resume_from_url(url, candidate_name=None):
    """
    Tarefa 8.2.3: Busca o PDF do candidato na URL fornecida pela Sólides/ATS
    e converte em um ContentFile que o Django consegue salvar no FileField.
    """
    if not url:
        return None
        
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            file_name = url.split('/')[-1]
            if not file_name.endswith('.pdf'):
                slug = str(candidate_name).lower().replace(" ", "_") if candidate_name else "candidato"
                file_name = f"cv_{slug}.pdf"
                
            return ContentFile(response.content, name=file_name)
        else:
            logger.error(f"[DOWNLOAD ERROR] Status {response.status_code} ao baixar PDF.")
            return None
    except requests.RequestException as e:
        logger.error(f"[DOWNLOAD EXCEPTION] Erro de rede ao baixar PDF: {str(e)}")
        return None


def send_analysis_to_external_system(analysis_id: int):
    '''
    Task 8.3.2: Sends AI analysis results to the configured callback_url.
    Payload includes candidate info, score, and summary.
    '''
    from brain.models import Analysis # Lazy import to avoid circular dependencies
    
    try:
        analysis = Analysis.objects.select_related('document', 'job').get(id=analysis_id)
        job = analysis.job
        
        # Se a vaga não tiver uma URL de retorno ou não houver job associado, ignoramos o envio
        if not job or not job.callback_url:
            logger.info(f"Vaga associada à análise {analysis_id} não possui callback_url configurada.")
            return False

        payload = {
            'vaga_id_externo': job.external_id,
            'crivopy_job_id': job.id,
            'candidato': {
                'nome': getattr(analysis.document, 'candidate_name', 'N/A'),
                'email': getattr(analysis.document, 'candidate_email', 'N/A'),
            },
            'analise_ia': {
                'score': getattr(analysis, 'score', 0), # garanta que esse campo exista no model Analysis
                'resumo': getattr(analysis, 'summary', ''), # garanta que esse campo exista no model Analysis
                'concluido_em': analysis.updated_at.isoformat() if hasattr(analysis, 'updated_at') else ''
            }
        }

        headers = {'Content-Type': 'application/json', 'User-Agent': 'Crivopy-Outbound-Webhook/1.0'}
        
        logger.info(f"Disparando notas do candidato {analysis.document.candidate_email} para {job.callback_url}...")
        response = requests.post(
            job.callback_url, 
            json=payload, 
            headers=headers, 
            timeout=15
        )

        # Task 8.1.3: Registrar a saída no log de auditoria
        IntegrationLog.objects.create(
            job=job,
            external_source='solides', # alterado para solides para centralizar o rastreio
            direction='OUTBOUND',
            payload=payload,
            status_code=response.status_code,
            success=response.ok,
            error_message=response.text if not response.ok else 'Enviado com sucesso'
        )

        return response.ok

    except Exception as e:
        logger.error(f'Falha no envio de webhook outbound: {str(e)}')
        return False