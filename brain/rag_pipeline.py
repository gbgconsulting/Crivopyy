import json
import logging
 
from django.conf import settings
from openai import OpenAI
 
from documents.models import Document
from hub.models import Job
 
from .pdf_extractor import extract_text_from_pdf, split_into_chunks
from .vector_store import index_document_chunks, search_similar_chunks
 
logger = logging.getLogger(__name__)
 
client = OpenAI(api_key=settings.OPENAI_API_KEY)
 
 
def build_prompt(job_description: str, relevant_chunks: list) -> str:
    '''Monta o prompt combinando requisitos da vaga e trechos do currículo.'''
    context = '\n---\n'.join(relevant_chunks)
 
    return f'''Você é um Especialista em RH técnico. Sua tarefa é analisar um currículo baseado em uma descrição de vaga.
 
DESCRIÇÃO DA VAGA:
{job_description}
 
TRECHOS RELEVANTES DO CURRÍCULO:
{context}
 
INSTRUÇÕES:
1. Responda obrigatoriamente em PORTUGUÊS BRASILEIRO. Jamais utilize palavras ou caracteres de outros idiomas.
2. Avalie a aderência do candidato à vaga.
3. Gere um score de 0 a 100 (onde 100 é o match perfeito).
4. Escreva um resumo executivo de até 4 frases destacando pontos fortes e lacunas.
 
Responda EXCLUSIVAMENTE em formato JSON:
{{"score": 85, "summary": "Texto do resumo aqui..."}}
'''
 
 
def call_llm(prompt: str) -> str:
    '''Chama a API OpenAI e retorna o texto gerado.'''
    model_name = getattr(settings, 'AGENT_MODEL', 'gpt-4o-mini')
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {'role': 'system', 'content': 'Você é um assistente de recrutamento imparcial e preciso.'},
            {'role': 'user', 'content': prompt},
        ],
        response_format={'type': 'json_object'},
        temperature=0.1,
    )
    return response.choices[0].message.content
 
 
def parse_llm_response(response_text: str) -> dict:
    '''Faz parse do JSON retornado pelo LLM.'''
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        logger.error('Failed to parse LLM JSON response')
        return {'score': 0, 'summary': 'Erro ao processar análise da IA.'}
 
 
def run_rag_analysis(document_id: int, job_id: int) -> dict:
    '''Pipeline RAG completo: extração → chunking → indexação → busca → geração.
 
    Args:
        document_id: ID do Document no banco.
        job_id: ID do Job no banco.
 
    Returns:
        Dict com 'score' (int 0-100) e 'summary' (str).
    '''
    try:
        job = Job.objects.get(pk=job_id)
        doc_record = Document.objects.get(pk=document_id)
 
        # 1. Extração de texto do PDF
        full_text = extract_text_from_pdf(doc_record.file.path)
        if not full_text:
            return {'score': 0, 'summary': 'O arquivo PDF não contém texto legível para análise.'}
 
        # 2. Chunking
        chunks = split_into_chunks(full_text)
 
        # 3. Indexação no ChromaDB
        index_document_chunks(document_id, chunks)
 
        # 4. Busca semântica — usa descrição da vaga como query
        relevant_chunks = search_similar_chunks(job.description, document_id, n_results=5)
 
        # 5. Geração via LLM
        prompt = build_prompt(job.description, relevant_chunks)
        raw_response = call_llm(prompt)
 
        # 6. Parse do resultado
        return parse_llm_response(raw_response)
 
    except Exception as exc:
        logger.error('RAG Pipeline failure for doc %s: %s', document_id, exc)
        return {'score': 0, 'summary': f'Falha no pipeline de análise: {exc}'}