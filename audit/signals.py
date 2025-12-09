from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps


def get_audit_model():
    return apps.get_model('audit', 'AuditLog')


@receiver(post_save)
def on_model_save(sender, instance, created, **kwargs):
    # Only watch select models (Party, Candidate, Voter, Vote) in users app
    if sender._meta.app_label != 'users':
        return

    name = sender.__name__
    if name not in ('Party', 'Candidate', 'Voter', 'Vote'):
        return

    AuditLog = get_audit_model()
    try:
        actor = getattr(instance, 'user', None)
    except Exception:
        actor = None

    AuditLog.objects.create(
        actor=actor if hasattr(actor, 'pk') else None,
        action='create' if created else 'update',
        target_model=f"users.{name}",
        target_repr=str(instance),
        details={},
    )


@receiver(post_delete)
def on_model_delete(sender, instance, **kwargs):
    if sender._meta.app_label != 'users':
        return

    name = sender.__name__
    if name not in ('Party', 'Candidate', 'Voter', 'Vote'):
        return

    AuditLog = get_audit_model()
    try:
        actor = getattr(instance, 'user', None)
    except Exception:
        actor = None

    AuditLog.objects.create(
        actor=actor if hasattr(actor, 'pk') else None,
        action='delete',
        target_model=f"users.{name}",
        target_repr=str(instance),
        details={},
    )
