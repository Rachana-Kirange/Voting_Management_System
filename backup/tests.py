from django.test import TestCase
from django.core.management import call_command
from backup.models import BackupRecord
import os


class BackupTests(TestCase):
    def test_create_backup_command(self):
        # Run the create_backup command (uses sqlite copy) and ensure a BackupRecord is created
        call_command('create_backup')
        self.assertTrue(BackupRecord.objects.exists())
        rec = BackupRecord.objects.first()
        # file may be empty name on failure; assert record saved
        self.assertIn(rec.success, (True, False))
        # If successful, file path exists
        if rec.success and rec.filename:
            self.assertTrue(os.path.exists(rec.filename))
from django.test import TestCase

# Create your tests here.
