from django.contrib import admin
from .models import IntegrationLog

@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    # Campos que vão aparecer na listagem geral do Admin
    list_display = ('id', 'external_source', 'direction', 'status_code', 'success', 'created_at')
    
    # Filtros que ficam na lateral direita da página
    list_filter = ('external_source', 'direction', 'success', 'created_at')
    
    # Campos que você pode clicar para buscar usando a barra de pesquisa
    search_fields = ('error_message', 'external_source')
    
    # Define quais campos serão apenas de leitura (já que são logs estruturados, é bom evitar edições manuais)
    readonly_fields = ('job', 'external_source', 'direction', 'payload', 'status_code', 'success', 'error_message', 'created_at')