from django.core.management.base import BaseCommand
from mail_receiver.models import Mailbox

class Command(BaseCommand):
    help = 'Aktualizuje foldery wszystkich aktywnych skrzynek pocztowych'

    def handle(self, *args, **options):
        mailboxes = Mailbox.objects.filter(is_active=True)
        for mailbox in mailboxes:
            try:
                mailbox.update_folders()
                self.stdout.write(self.style.SUCCESS(f'Zaktualizowano foldery dla {mailbox.name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Błąd dla {mailbox.name}: {str(e)}'))