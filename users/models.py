from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from elections.models import Election


# =========================
# CUSTOM USER MANAGER
# =========================
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("Username must be set")
        if not email:
            raise ValueError("Email must be set")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)


# =========================
# CUSTOM USER MODEL
# =========================
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("voter", "Voter"),
        ("candidate", "Candidate"),
    ]

    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="voter")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


# =========================
# PARTY MODEL
# =========================
class Party(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# =========================
# CANDIDATE MODEL
# =========================
class Candidate(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidate_profile",
    )

    elections = models.ManyToManyField(
        Election, blank=True, related_name="candidates"
    )

    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    area = models.CharField(max_length=100)
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)

    def clean(self):
        if self.user and self.user.role != "candidate":
            raise ValidationError("Linked user must have candidate role.")

    def __str__(self):
        return f"{self.name} ({self.party.name})"


# =========================
# CAMPAIGN MODEL
# =========================
class Campaign(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.name} - {self.election.title}"


# =========================
# VOTER MODEL
# =========================
class Voter(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voter_id = models.CharField(max_length=20, unique=True)
    mobile_no = models.CharField(max_length=15)
    address = models.TextField()

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="pending",
    )
    verification_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# =========================
# VOTE MODEL (ONLY ONE)
# =========================
class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    election = models.ForeignKey(
    'elections.Election',
    on_delete=models.CASCADE,
    related_name='user_votes'
)

    voted_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["voter", "election"],
                name="unique_vote_per_voter_per_election",
            )
        ]

    def __str__(self):
        return f"{self.voter.user.username} voted in {self.election.title}"


# =========================
# NOTIFICATION MODEL
# =========================
class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ("registration", "Registration"),
        ("verification", "Verification Status"),
        ("election_open", "Election Open"),
        ("election_reminder", "Election Reminder"),
        ("vote_confirmation", "Vote Confirmation"),
        ("results_available", "Results Available"),
        ("system", "System Alert"),
    ]

    voter = models.ForeignKey(
        Voter, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default="system"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    election = models.ForeignKey(
        Election, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.voter.user.username} - {self.title}"
