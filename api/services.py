from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from lab.models import HistoriqueAction, Notification, User


def log_history(demande, action, actor):
    HistoriqueAction.objects.create(
        demande=demande,
        action=action,
        acteur=actor,
    )


def notify_user(user, message):
    Notification.objects.create(user=user, message=message)
    if user.email:
        send_mail(
            subject="Mise a jour LabResa",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


def notify_role_users(role_values, message):
    users = User.objects.filter(role__in=role_values, is_active=True).exclude(email="")
    with transaction.atomic():
        Notification.objects.bulk_create(
            [Notification(user=user, message=message) for user in users],
            batch_size=200,
        )
    for user in users:
        send_mail(
            subject="Mise a jour LabResa",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

