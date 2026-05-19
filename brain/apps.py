# brain/apps.py

from django.apps import AppConfig

class BrainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'brain'
    verbose_name = 'Inteligência e Análise'

    def ready(self):
        import brain.signals # Conecta o gatilho de saída