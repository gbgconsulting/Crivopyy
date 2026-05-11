import logging
from typing import Any, List

import chromadb
from chromadb.config import Settings
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

OPENAI_EMBEDDINGS_COLLECTION = 'crivopy_resumes_openai'

chroma_client = chromadb.PersistentClient(
    path=str(settings.CHROMA_DB_PATH),
    settings=Settings(allow_reset=True),
)


_openai_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _embed_openai_batch(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    if not settings.OPENAI_API_KEY:
        raise ValueError('OPENAI_API_KEY is not configured')
    model_name = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    resp = _get_openai_client().embeddings.create(model=model_name, input=texts)
    ordered = sorted(resp.data, key=lambda d: d.index)
    return [row.embedding for row in ordered]


def get_or_create_collection(collection_name: str = OPENAI_EMBEDDINGS_COLLECTION):
    '''Return o client ChromaDB collection (embedding OpenAI, dimensões distintas do índice legado MiniLM).'''
    return chroma_client.get_or_create_collection(name=collection_name)


def index_document_chunks(document_id: int, chunks: List[str]) -> None:
    '''
    Generate embeddings via OpenAI and index chunks into ChromaDB.
    '''
    if not chunks:
        return

    collection = get_or_create_collection()

    embeddings = _embed_openai_batch(chunks)

    ids = [f'doc_{document_id}_chunk_{i}' for i in range(len(chunks))]
    metadatas: List[dict[str, Any]] = [{'document_id': document_id} for _ in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=chunks,
    )


def search_similar_chunks(query: str, document_id: int, n_results: int = 5) -> List[str]:
    '''Semantic search filtered by document_id.'''
    collection = get_or_create_collection()

    query_embeddings = _embed_openai_batch([query])
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        where={'document_id': document_id},
    )

    return results['documents'][0] if results['documents'] else []


def delete_document_chunks(document_id: int) -> None:
    '''Remove all chunks associated with a specific document.'''
    collection = get_or_create_collection()
    collection.delete(where={'document_id': document_id})
