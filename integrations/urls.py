from django.urls import path
from .views import SolidesWebhookView

app_name = 'integrations'

urlpatterns = [
    # URL que será cadastrada na Sólides: https://seu-dominio.com/integrations/solides/webhook/
    path('solides/webhook/', SolidesWebhookView.as_view(), name='solides-webhook'),
]