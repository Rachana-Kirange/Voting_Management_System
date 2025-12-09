from django.db import models
from django.conf import settings


class AuditLog(models.Model):
	"""Record of actions performed in the system for traceability."""
	ACTION_CHOICES = [
		('create', 'Create'),
		('update', 'Update'),
		('delete', 'Delete'),
		('backup', 'Backup'),
		('other', 'Other'),
	]

	actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	action = models.CharField(max_length=20, choices=ACTION_CHOICES)
	target_model = models.CharField(max_length=200, blank=True)
	target_repr = models.TextField(blank=True)
	details = models.JSONField(default=dict, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.get_action_display()} by {self.actor or 'system'} on {self.target_model} — {self.target_repr}"
