from django.urls import path
from .views import (
    DashboardView, 
    JobListView, 
    JobCreateView, 
    JobUpdateView, 
    JobArchiveView,
    PipelineDataView,
)

app_name = 'hub'

urlpatterns = [
    # Rota principal do Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Rotas de gerenciamento de vagas (Sprint 3)
    path('vagas/', JobListView.as_view(), name='job-list'),
    path('vagas/nova/', JobCreateView.as_view(), name='job-create'),
    path('vagas/<int:pk>/editar/', JobUpdateView.as_view(), name='job-update'),
    path('vagas/<int:pk>/arquivar/', JobArchiveView.as_view(), name='job-archive'),
    path('api/pipeline-data/', PipelineDataView.as_view(), name='pipeline-data-api'),

]