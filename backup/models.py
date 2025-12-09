from django.db import models
from django.conf import settings


class BackupRecord(models.Model):
	performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	filename = models.CharField(max_length=400)
	created_at = models.DateTimeField(auto_now_add=True)
	size = models.BigIntegerField(null=True, blank=True)
	note = models.TextField(blank=True)
	success = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Backup {self.filename} ({'OK' if self.success else 'FAILED'})"
