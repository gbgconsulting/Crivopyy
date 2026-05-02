from django.urls import path
from django.views.generic import TemplateView # Necessário para a página de sucesso simples
from . import views

'''
URL configuration for the documents application.
Handles candidate resume management and status updates.
'''

urlpatterns = [
    # --- ROTAS INTERNAS (RECRUTADOR) ---
    
    # Task 4.5.2: List documents for a specific job
    path(
        'vagas/<int:job_pk>/documentos/', 
        views.DocumentListView.as_view(), 
        name='document-list'
    ),
    
    # Task 4.5.3: Upload a new resume for a specific job
    path(
        'vagas/<int:job_pk>/documentos/upload/', 
        views.DocumentUploadView.as_view(), 
        name='document-upload'
    ),
    
    # Task 4.5.4: Update the status of a specific document
    path(
        'documentos/<int:pk>/status/', 
        views.DocumentStatusUpdateView.as_view(), 
        name='document-status'
    ),
    
    # Task 4.5.5: Delete a document record
    path(
        'documentos/<int:pk>/excluir/', 
        views.DocumentDeleteView.as_view(), 
        name='document-delete'
    ),

    # --- ROTAS PÚBLICAS (CANDIDATOS) ---

    # Rota de Inscrição: /candidatar/70816796-c02d-4a11-ac3d-b5225d269744/
    path(
        'candidatar/<uuid:token>/', 
        views.PublicApplyView.as_view(), 
        name='public-apply'
    ),

    # Rota de Sucesso após inscrição
    path('candidatar/<uuid:token>/sucesso/', views.PublicSuccessView.as_view(), name='apply-success'
         
    
    ),

]