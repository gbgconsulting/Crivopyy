# agents/hr_agent.py
#
# Agente de IA especializado em Recrutamento e Seleção — Crivopy
#
# Implementado com LangChain 1.0 usando create_agent + @tool decorator.
# As tools são definidas dentro de run_hr_agent para capturar job_id e
# user_id diretamente no escopo — abordagem simples e sem bugs de closure.
 
from __future__ import annotations
 
import logging
from typing import Any
 
from django.conf import settings
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
 
logger = logging.getLogger(__name__)
 
# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
 
SYSTEM_PROMPT = """Você é um especialista sênior em Recrutamento e Seleção com profundo
conhecimento em análise de perfis, triagem de currículos e estratégias de atração de talentos.
 
Seu papel é auxiliar recrutadores a tomar decisões mais inteligentes sobre os candidatos
de uma vaga específica, fornecendo análises, comparações e recomendações estratégicas com
base nos dados reais do sistema.
 
Diretrizes obrigatórias:
- Responda SEMPRE em português brasileiro, com linguagem profissional e objetiva.
- Baseie suas análises EXCLUSIVAMENTE nos dados retornados pelas ferramentas disponíveis.
- NUNCA invente candidatos, scores, nomes ou informações que não estejam nos dados.
- Quando os dados forem insuficientes para uma análise, informe isso claramente.
- Use as ferramentas quantas vezes forem necessárias para compor uma resposta completa.
- Ao comparar candidatos, cite nomes e scores de forma objetiva.
- Quando identificar lacunas na base de candidatos em relação aos requisitos da vaga, aponte-as.
 
Você tem acesso às seguintes ferramentas para consultar os dados da vaga atual:
- list_candidates: lista todos os candidatos com status e score
- get_candidate_detail: detalhes completos de um candidato específico
- get_job_summary: resumo da vaga com requisitos e estatísticas gerais
- get_top_candidates: ranking dos candidatos com maiores scores
- get_candidates_by_status: candidatos filtrados por status de triagem


REGRA CRÍTICA SOBRE FERRAMENTAS:
- Quando list_candidates ou get_top_candidates retornarem candidatos, cada linha contém
  [document_id:X] no início. Você DEVE usar exatamente esse número X ao chamar
  get_candidate_detail. Nunca tente adivinhar ou inventar um document_id.
- Sempre use get_candidate_detail com o document_id exato retornado pela listagem
  antes de fazer qualquer análise comparativa.
"""
 
# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------
 
 
def _get_job_model():
    from hub.models import Job  # noqa: PLC0415
    return Job
 
 
def _get_document_model():
    from documents.models import Document  # noqa: PLC0415
    return Document
 
 
def _get_analysis_model():
    from brain.models import Analysis  # noqa: PLC0415
    return Analysis
 
 
def _validate_job_ownership(job_id: int, user_id: int) -> Any | None:
    '''Retorna o Job se pertencer ao user_id, None caso contrário.'''
    Job = _get_job_model()
    try:
        return Job.objects.get(id=job_id, user_id=user_id)
    except Job.DoesNotExist:
        return None
 
 
def _format_candidate_row(doc, analysis=None) -> str:
    '''Formata uma linha de candidato para exibição em texto.'''
    score_str = (
        f'Score RAG: {analysis.score}/100'
        if analysis and analysis.score is not None
        else 'Sem análise RAG'
    )
    status_labels = {
        'pending': 'Pendente',
        'reviewing': 'Em análise',
        'approved': 'Aprovado',
        'rejected': 'Reprovado',
    }
    status_str = status_labels.get(doc.status, doc.status)
    email_str = f' | {doc.candidate_email}' if doc.candidate_email else ''
    return f'- [document_id:{doc.id}] {doc.candidate_name}{email_str} | Status: {status_str} | {score_str}'

 
 
def _serialize_history(history: list[dict]) -> list:
    '''Converte o histórico armazenado no banco para objetos de mensagem do LangChain.'''
    from langchain_core.messages import AIMessage, HumanMessage
 
    messages = []
    for entry in history:
        role = entry.get('role', '')
        content = entry.get('content', '')
        if role == 'human':
            messages.append(HumanMessage(content=content))
        elif role == 'ai':
            messages.append(AIMessage(content=content))
    return messages
 
 
def _get_model() -> ChatOpenAI:
    '''Retorna o modelo de linguagem configurado para o agente.'''
    model_name = getattr(settings, 'AGENT_MODEL', 'gpt-4o-mini')
    return ChatOpenAI(model=model_name, temperature=0.3)
 
 
# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------
 
 
def run_hr_agent(
    job_id: int,
    user_id: int,
    user_message: str,
    history: list[dict] | None = None,
) -> dict:
    '''Executa o Agente de RH para uma pergunta do usuário sobre uma vaga.
 
    As tools são definidas aqui dentro para capturar job_id e user_id
    diretamente no escopo da função, sem closures complexas ou partials.
 
    Args:
        job_id: ID da vaga em contexto.
        user_id: ID do usuário autenticado.
        user_message: Pergunta em linguagem natural.
        history: Histórico anterior como lista de dicts {'role', 'content'}.
 
    Returns:
        Dict com 'response' (str) e 'history' (list).
        Em caso de erro, inclui chave 'error' e resposta amigável.
    '''
    if history is None:
        history = []
 
    # ------------------------------------------------------------------
    # Tools definidas aqui — job_id e user_id capturados no escopo local
    # ------------------------------------------------------------------
 
    @tool
    def list_candidates(status_filter: str = '') -> str:
        '''Lista todos os candidatos da vaga com nome, e-mail, status e score RAG.
 
        Args:
            status_filter: Filtro opcional. Valores: pending, reviewing, approved, rejected.
                           Deixe vazio para listar todos.
        '''
        try:
            job = _validate_job_ownership(job_id, user_id)
            if not job:
                return 'Vaga não encontrada ou sem permissão de acesso.'
 
            Document = _get_document_model()
            Analysis = _get_analysis_model()
 
            docs = Document.objects.filter(job_id=job_id)
            if status_filter:
                docs = docs.filter(status=status_filter)
 
            if not docs.exists():
                suffix = f' com status "{status_filter}"' if status_filter else ''
                return f'Nenhum candidato encontrado para a vaga "{job.title}"{suffix}.'
 
            analyses = {
                a.document_id: a
                for a in Analysis.objects.filter(document__job_id=job_id, rag_status='done')
            }
 
            lines = [f'Candidatos da vaga "{job.title}" ({docs.count()} encontrado(s)):\n']
            for doc in docs.order_by('-created_at'):
                lines.append(_format_candidate_row(doc, analyses.get(doc.id)))
 
            return '\n'.join(lines)
        except Exception as exc:
            logger.error('list_candidates error: %s', exc)
            return 'Não foi possível listar os candidatos. Tente novamente.'
 
    @tool
    def get_candidate_detail(document_id: int) -> str:
        '''Retorna detalhes completos de um candidato: nome, e-mail, status,
        notas do recrutador, score RAG e resumo da análise.
 
        Args:
            document_id: ID do documento (currículo) do candidato.
        '''
        try:
            job = _validate_job_ownership(job_id, user_id)
            if not job:
                return 'Vaga não encontrada ou sem permissão de acesso.'
 
            Document = _get_document_model()
            Analysis = _get_analysis_model()
 
            try:
                doc = Document.objects.get(id=document_id, job_id=job_id)
            except Document.DoesNotExist:
                return 'Candidato não encontrado para esta vaga.'
 
            status_labels = {
                'pending': 'Pendente',
                'reviewing': 'Em análise',
                'approved': 'Aprovado',
                'rejected': 'Reprovado',
            }
 
            lines = [
                f'Candidato: {doc.candidate_name}',
                f'E-mail: {doc.candidate_email or "Não informado"}',
                f'Status: {status_labels.get(doc.status, doc.status)}',
                f'Enviado em: {doc.created_at.strftime("%d/%m/%Y")}',
            ]
 
            if doc.notes:
                lines.append(f'Notas do recrutador: {doc.notes}')
 
            analysis = Analysis.objects.filter(
                document_id=document_id, rag_status='done'
            ).first()
 
            if analysis:
                lines.append(f'\nAnálise de IA (Score: {analysis.score}/100):')
                lines.append(analysis.summary or 'Resumo não disponível.')
            else:
                lines.append('\nAnálise de IA: ainda não realizada para este candidato.')
 
            return '\n'.join(lines)
        except Exception as exc:
            logger.error('get_candidate_detail error: %s', exc)
            return 'Não foi possível obter os detalhes do candidato. Tente novamente.'
 
    @tool
    def get_job_summary() -> str:
        '''Retorna resumo completo da vaga: título, descrição, requisitos,
        total de candidatos por status e score médio RAG.
        '''
        try:
            job = _validate_job_ownership(job_id, user_id)
            if not job:
                return 'Vaga não encontrada ou sem permissão de acesso.'
 
            Document = _get_document_model()
            Analysis = _get_analysis_model()
 
            status_labels = {
                'pending': 'Pendente',
                'reviewing': 'Em análise',
                'approved': 'Aprovado',
                'rejected': 'Reprovado',
            }
            job_status_labels = {
                'active': 'Ativa',
                'paused': 'Pausada',
                'archived': 'Arquivada',
            }
 
            total = Document.objects.filter(job_id=job_id).count()
            by_status = {}
            for key, label in status_labels.items():
                count = Document.objects.filter(job_id=job_id, status=key).count()
                if count:
                    by_status[label] = count
 
            analyses = Analysis.objects.filter(
                document__job_id=job_id, rag_status='done', score__isnull=False
            )
            avg_score = None
            if analyses.exists():
                scores = [a.score for a in analyses if a.score is not None]
                avg_score = round(sum(scores) / len(scores), 1) if scores else None
 
            lines = [
                f'Vaga: {job.title}',
                f'Status: {job_status_labels.get(job.status, job.status)}',
                f'Criada em: {job.created_at.strftime("%d/%m/%Y")}',
            ]
 
            if job.description:
                lines.append(f'\nRequisitos / Descrição:\n{job.description}')
 
            lines.append(f'\nEstatísticas (total: {total}):')
            if by_status:
                for label, count in by_status.items():
                    lines.append(f'  - {label}: {count}')
            else:
                lines.append('  Nenhum candidato cadastrado ainda.')
 
            if avg_score is not None:
                lines.append(f'\nScore médio RAG: {avg_score}/100')
            else:
                lines.append('\nNenhum candidato com análise RAG concluída.')
 
            return '\n'.join(lines)
        except Exception as exc:
            logger.error('get_job_summary error: %s', exc)
            return 'Não foi possível obter o resumo da vaga. Tente novamente.'
 
    @tool
    def get_top_candidates(limit: int = 5) -> str:
        '''Retorna o ranking dos candidatos com maiores scores RAG, do maior para o menor.
 
        Args:
            limit: Número de candidatos a retornar (padrão: 5, máximo: 20).
        '''
        try:
            job = _validate_job_ownership(job_id, user_id)
            if not job:
                return 'Vaga não encontrada ou sem permissão de acesso.'
 
            Analysis = _get_analysis_model()
 
            limit = min(max(1, limit), 20)
 
            top = (
                Analysis.objects
                .filter(document__job_id=job_id, rag_status='done', score__isnull=False)
                .select_related('document')
                .order_by('-score')[:limit]
            )
 
            if not top:
                return (
                    f'Nenhum candidato com análise RAG concluída para a vaga "{job.title}". '
                    'Execute a análise de IA nos candidatos primeiro.'
                )
 
            status_labels = {
                'pending': 'Pendente',
                'reviewing': 'Em análise',
                'approved': 'Aprovado',
                'rejected': 'Reprovado',
            }
 
            lines = [f'Top {limit} candidatos por score RAG — vaga "{job.title}":\n']
            for i, analysis in enumerate(top, start=1):
                doc = analysis.document
                status_str = status_labels.get(doc.status, doc.status)
                lines.append(
                    f'{i}. [document_id:{doc.id}] {doc.candidate_name} | Score: {analysis.score}/100 | Status: {status_str}'

                )
 
            return '\n'.join(lines)
        except Exception as exc:
            logger.error('get_top_candidates error: %s', exc)
            return 'Não foi possível obter o ranking de candidatos. Tente novamente.'
 
    @tool
    def get_candidates_by_status(status: str) -> str:
        '''Retorna candidatos filtrados por um status específico de triagem.
 
        Args:
            status: Status dos candidatos. Valores válidos:
                pending (Pendente), reviewing (Em análise),
                approved (Aprovado), rejected (Reprovado).
        '''
        try:
            job = _validate_job_ownership(job_id, user_id)
            if not job:
                return 'Vaga não encontrada ou sem permissão de acesso.'
 
            valid_statuses = ['pending', 'reviewing', 'approved', 'rejected']
            status_labels = {
                'pending': 'Pendente',
                'reviewing': 'Em análise',
                'approved': 'Aprovado',
                'rejected': 'Reprovado',
            }
 
            if status not in valid_statuses:
                return (
                    f'Status inválido: "{status}". '
                    f'Valores válidos: {", ".join(valid_statuses)}.'
                )
 
            Document = _get_document_model()
            Analysis = _get_analysis_model()
 
            docs = Document.objects.filter(job_id=job_id, status=status)
            label = status_labels[status]
 
            if not docs.exists():
                return f'Nenhum candidato com status "{label}" para a vaga "{job.title}".'
 
            analyses = {
                a.document_id: a
                for a in Analysis.objects.filter(
                    document__job_id=job_id, rag_status='done'
                )
            }
 
            lines = [f'Candidatos com status "{label}" na vaga "{job.title}" ({docs.count()}):\n']
            for doc in docs.order_by('-created_at'):
                lines.append(_format_candidate_row(doc, analyses.get(doc.id)))
 
            return '\n'.join(lines)
        except Exception as exc:
            logger.error('get_candidates_by_status error: %s', exc)
            return 'Não foi possível filtrar os candidatos. Tente novamente.'
 
    # ------------------------------------------------------------------
    # Execução do agente
    # ------------------------------------------------------------------
 
    scoped_tools = [
        list_candidates,
        get_candidate_detail,
        get_job_summary,
        get_top_candidates,
        get_candidates_by_status,
    ]
 
    try:
        max_history = getattr(settings, 'AGENT_MAX_HISTORY', 10)
        trimmed_history = history[-(max_history):]
        prior_messages = _serialize_history(trimmed_history)
 
        from langchain_core.messages import HumanMessage
 
        model = _get_model()
        agent = create_agent(model, tools=scoped_tools, system_prompt=SYSTEM_PROMPT)
 
        input_messages = prior_messages + [HumanMessage(content=user_message)]
        result = agent.invoke({'messages': input_messages})
 
        response_message = result['messages'][-1]
        response_content = (
            response_message.content
            if hasattr(response_message, 'content')
            else str(response_message)
        )
 
        updated_history = trimmed_history + [
            {'role': 'human', 'content': user_message},
            {'role': 'ai', 'content': response_content},
        ]
 
        return {
            'response': response_content,
            'history': updated_history,
        }
 
    except Exception as exc:
        logger.error('run_hr_agent error (job_id=%s, user_id=%s): %s', job_id, user_id, exc)
        return {
            'response': (
                'Desculpe, não foi possível processar sua pergunta no momento. '
                'Verifique se a chave da API está configurada e tente novamente.'
            ),
            'history': history,
            'error': str(exc),
        }
 