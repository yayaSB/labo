from django.core.management.base import BaseCommand
from django.utils import timezone

from lab.models import Composant, DemandeWorkflow, User


class Command(BaseCommand):
    help = "Seed complet pour la plateforme API LabResa (roles + composants + demandes)."

    def handle(self, *args, **options):
        users = [
            ("admin3ph", "SERVICE_3PH", "admin3ph@labresa.local"),
            ("encadrant1", "ENCADRANT", "encadrant1@labresa.local"),
            ("labo1", "LABRESPO", "labo1@labresa.local"),
            ("achat1", "SERVICE_ACHAT", "achat1@labresa.local"),
            ("etudiant1", "ETUDIANT", "etudiant1@labresa.local"),
            ("etudiant2", "ETUDIANT", "etudiant2@labresa.local"),
        ]

        created = {}
        for username, role, email in users:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": role,
                    "is_active": True,
                    "first_name": username.capitalize(),
                    "last_name": "LabResa",
                },
            )
            user.role = role
            user.email = email
            user.set_password("LabResa123!")
            user.save()
            created[username] = user

        created["encadrant1"].departement = "Electronique"
        created["encadrant1"].save(update_fields=["departement"])

        created["etudiant1"].classe = "GI-3A"
        created["etudiant1"].encadrant = created["encadrant1"]
        created["etudiant1"].save(update_fields=["classe", "encadrant"])
        created["etudiant1"].encadrants.set([created["encadrant1"]])

        created["etudiant2"].classe = "GI-3A"
        created["etudiant2"].encadrant = created["encadrant1"]
        created["etudiant2"].save(update_fields=["classe", "encadrant"])
        created["etudiant2"].encadrants.set([created["encadrant1"]])

        c1, _ = Composant.objects.get_or_create(
            reference="RES-220",
            defaults={
                "nom": "Resistance 220 ohm",
                "quantite_disponible": 120,
                "seuil_alerte": 30,
                "localisation": "Rack A1",
            },
        )
        c2, _ = Composant.objects.get_or_create(
            reference="ARD-UNO",
            defaults={
                "nom": "Arduino Uno",
                "quantite_disponible": 3,
                "seuil_alerte": 4,
                "localisation": "Rack B2",
            },
        )

        DemandeWorkflow.objects.get_or_create(
            etudiant=created["etudiant1"],
            composant=c1,
            quantite=10,
            defaults={"statut": DemandeWorkflow.Statut.EN_ATTENTE_ENCADRANT},
        )
        DemandeWorkflow.objects.get_or_create(
            etudiant=created["etudiant2"],
            composant=c2,
            quantite=5,
            defaults={"statut": DemandeWorkflow.Statut.EN_ATTENTE_LABO},
        )

        self.stdout.write(self.style.SUCCESS("Seed API LabResa termine."))
        self.stdout.write("Mot de passe commun: LabResa123!")
        self.stdout.write(f"Date seed: {timezone.now():%Y-%m-%d %H:%M:%S}")
