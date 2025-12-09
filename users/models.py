from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Custom user manager where username and email are required fields."""
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('The username must be set')
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('voter', 'Voter'),
        ('candidate', 'Candidate'),
        ('poll_officer', 'Poll Officer'),
    ]

    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(choices=ROLE_CHOICES, default='voter', max_length=20)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.username

# -----------------------------------------
# 1. PARTY TABLE
# -----------------------------------------
class Party(models.Model):
    name = models.CharField(max_length=100)
    # symbol field removed (no image uploads required for parties)

    def __str__(self):
        return self.name

# -----------------------------------------
# 2. CANDIDATE TABLE
# -----------------------------------------
class Candidate(models.Model):
    # Optional link to a User account - a candidate may also be a user in the system
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidate_profile')
    # candidate can participate in one or more elections
    elections = models.ManyToManyField('elections.Election', blank=True, related_name='candidates')
    name = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    age = models.IntegerField()
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    area = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.party.name})"

# -----------------------------------------
# 3. VOTER TABLE
# -----------------------------------------
class Voter(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voter_id = models.CharField(max_length=20, unique=True)
    mobile = models.CharField(max_length=15)
    address = models.TextField()
    has_voted = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    verification_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username

# -----------------------------------------
# 4. VOTE TABLE
# -----------------------------------------
class Vote(models.Model):
    # one voter can cast many votes (one vote per election is enforced by unique_together)
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    election = models.ForeignKey('elections.Election', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voter.user.username} → {self.candidate.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['voter', 'election'], name='unique_vote_per_voter_per_election')
        ]

# -----------------------------------------
# 5. NOTIFICATION TABLE
# -----------------------------------------
class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('registration', 'Registration'),
        ('verification', 'Verification Status'),
        ('election_open', 'Election Open'),
        ('election_reminder', 'Election Reminder'),
        ('vote_confirmation', 'Vote Confirmation'),
        ('results_available', 'Results Available'),
        ('system', 'System Alert'),
    ]

    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    election = models.ForeignKey('elections.Election', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.voter.user.username} - {self.title}"
