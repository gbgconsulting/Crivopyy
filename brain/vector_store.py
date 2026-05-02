import chromadb
from chromadb.config import Settings
from django.conf import settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# Task 5B.3.2: Initialize persistent ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=str(settings.CHROMA_DB_PATH),
    settings=Settings(allow_reset=True)
)

_model_instance = None

def get_embedding_model():
    """Carrega o modelo apenas quando for necessário (Lazy Loading)."""
    global _model_instance
    if _model_instance is None:
        print('--- CARREGANDO MODELO DE IA PELA PRIMEIRA VEZ ---')
        _model_instance = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model_instance

def get_or_create_collection(collection_name: str = 'crivopy_resumes'):
    '''
    Task 5B.3.3: Return the ChromaDB collection.
    '''
    return chroma_client.get_or_create_collection(name=collection_name)

def index_document_chunks(document_id: int, chunks: List[str]) -> None:
    '''
    Task 5B.3.4: Generate embeddings and index chunks into ChromaDB.
    '''
    if not chunks:
        return

    collection = get_or_create_collection()
    
    # CORREÇÃO AQUI: Chamamos a função para obter o modelo
    model = get_embedding_model()
    embeddings = model.encode(chunks).tolist()
    
    ids = [f'doc_{document_id}_chunk_{i}' for i in range(len(chunks))]
    metadatas = [{'document_id': document_id} for _ in range(len(chunks))]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=chunks
    )

def search_similar_chunks(query: str, document_id: int, n_results: int = 5) -> List[str]:
    '''
    Task 5B.3.5: Search semanticly similar chunks filtered by document_id.
    '''
    collection = get_or_create_collection()
    
    # CORREÇÃO AQUI: Chamamos a função para obter o modelo
    model = get_embedding_model()
    query_embedding = model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where={'document_id': document_id}
    )
    
    # CORREÇÃO DA LINHA 73: Adicionado o '[]' após o else
    return results['documents'][0] if results['documents'] else []

def delete_document_chunks(document_id: int) -> None:
    '''
    Task 5B.3.6: Remove all chunks associated with a specific document.
    '''
    collection = get_or_create_collection()
    collection.delete(where={'document_id': document_id})