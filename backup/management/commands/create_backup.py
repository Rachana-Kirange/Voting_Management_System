import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Create a project backup: copies sqlite database or dumps data to a JSON file and records a BackupRecord.'

    def add_arguments(self, parser):
        parser.add_argument('--user', help='Username who triggered the backup (optional)')

    def handle(self, *args, **options):
        user = options.get('user')
        # import lazily to avoid startup circular imports
        from backup.models import BackupRecord
        performed_by = None
        if user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                performed_by = User.objects.get(username=user)
            except User.DoesNotExist:
                performed_by = None

        out_dir = getattr(settings, 'BASE_DIR', None)
        if out_dir is None:
            out_dir = os.getcwd()

        backups_dir = os.path.join(out_dir, 'backups')
        os.makedirs(backups_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        default_db = settings.DATABASES.get('default', {})
        engine = default_db.get('ENGINE', '')

        record = BackupRecord(performed_by=performed_by)
        try:
            if 'sqlite3' in engine:
                db_name = default_db.get('NAME')
                if not db_name or not os.path.exists(db_name):
                    raise RuntimeError('SQLite DB file not found')

                dest = os.path.join(backups_dir, f'db_backup_{timestamp}.sqlite3')
                shutil.copy2(db_name, dest)
                record.filename = dest
                record.size = os.path.getsize(dest)
                record.success = True
                record.note = 'SQLite file copied'
            else:
                # fallback to dumpdata
                dest = os.path.join(backups_dir, f'dump_{timestamp}.json')
                call_command('dumpdata', '--natural-primary', '--natural-foreign', '-e', 'contenttypes', '-e', 'auth.permission', stdout=open(dest, 'w'))
                record.filename = dest
                record.size = os.path.getsize(dest)
                record.success = True
                record.note = 'dumpdata produced JSON'

        except Exception as exc:
            record.filename = ''
            record.success = False
            record.note = str(exc)

        record.save()
        if record.success:
            self.stdout.write(self.style.SUCCESS(f'Backup created: {record.filename}'))
        else:
            self.stdout.write(self.style.ERROR(f'Backup failed: {record.note}'))
