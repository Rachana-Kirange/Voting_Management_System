from django.db import models


class Election(models.Model):
	ELECTION_TYPES = [
		('single', 'Single Winner'),
		('multi', 'Multi Winner'),
		('referendum', 'Referendum'),
	]

	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	election_type = models.CharField(max_length=30, choices=ELECTION_TYPES, default='single')
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	is_active = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.title
