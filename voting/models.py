from django.db import models
from django.conf import settings
from elections.models import Election
from users.models import Candidate

User = settings.AUTH_USER_MODEL

class Vote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey(
        Election, 
        on_delete=models.CASCADE, 
        related_name='voting_votes'  # <-- add this
    )
    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE, 
        related_name='voting_votes'  # <-- add this
    )
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'election')

    def __str__(self):
        return f"{self.voter} voted in {self.election}"
