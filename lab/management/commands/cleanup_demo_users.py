from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from lab.models import (
    AffectationGroupe,
    Demande,
    DemandeWorkflow,
    MembreGroupe,
    MouvementStock,
    Notification,
    User,
)


class Command(BaseCommand):
    help = "Supprime les comptes de demonstration seeds et leurs traces principales."

    DEMO_USERNAMES = [
        "labrespo",
        "service3ph",
        "serviceachat",
        "encadrant1",
        "encadrant2",
        "etudiant1",
        "etudiant2",
        "etudiant3",
        "admin3ph",
        "labo1",
        "achat1",
        "enseignant1",
        "enseignant2",
    ]

    def handle(self, *args, **options):
        demo_users = User.objects.filter(username__in=self.DEMO_USERNAMES)
        usernames = list(demo_users.values_list("username", flat=True))

        if not usernames:
            self.stdout.write("Aucun compte de demonstration a supprimer.")
            return

        with transaction.atomic():
            User.objects.filter(encadrant__in=demo_users).update(encadrant=None)
            MouvementStock.objects.filter(valide_par__in=demo_users).delete()
            AffectationGroupe.objects.filter(
                Q(enseignant__in=demo_users) | Q(attribue_par__in=demo_users)
            ).delete()
            MembreGroupe.objects.filter(etudiant__in=demo_users).delete()
            Demande.objects.filter(etudiant__in=demo_users).delete()
            DemandeWorkflow.objects.filter(etudiant__in=demo_users).delete()
            Notification.objects.filter(user__in=demo_users).delete()
            deleted_count, _ = demo_users.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Comptes demo supprimes ({deleted_count} lignes impactees): {', '.join(usernames)}"
            )
        )
