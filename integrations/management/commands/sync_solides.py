from django.core.management.base import BaseCommand, CommandError
from integrations.services import sync_jobs_from_solides
from users.models import User

class Command(BaseCommand):
    help = 'Sincroniza as vagas da Sólides para o Crivopy'

    def add_arguments(self, parser):
        # Precisamos de um ID de usuário para ser o "dono" das vagas importadas
        parser.add_argument('user_id', type=int, help='ID do usuário recrutador no Crivopy')

    def handle(self, *args, **options):
        user_id = options['user_id']
        
        if not User.objects.filter(id=user_id).exists():
            raise CommandError(f"Usuário com ID {user_id} não encontrado.")

        self.stdout.write(self.style.WARNING('Iniciando sincronização com Sólides...'))
        
        success = sync_jobs_from_solides(user_id)
        
        if success:
            self.stdout.write(self.style.SUCCESS('Vagas sincronizadas com sucesso!'))
        else:
            self.stdout.write(self.style.ERROR('Falha na sincronização. Verifique os logs no Admin.'))