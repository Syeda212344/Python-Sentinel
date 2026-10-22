from django.core.management.base import BaseCommand
from sentinel.services import seed_historical_data
class Command(BaseCommand):
    help='Load clearly labeled simulated events and alerts for 75 calendar days (idempotent).'
    def add_arguments(self,parser):
        parser.add_argument('--reset',action='store_true',help='Delete and recreate only SIMULATED records.')
    def handle(self,*args,**options):
        outcome=seed_historical_data(reset=options['reset'])
        self.stdout.write(self.style.SUCCESS(f"Synthetic event records created: {outcome['created']}. Already seeded: {outcome['already_seeded']}"))
