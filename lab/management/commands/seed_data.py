from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from lab.models import (
    AffectationGroupe,
    Demande,
    DemandeNouveauMateriel,
    Groupe,
    LigneDemande,
    Materiel,
    MembreGroupe,
    User,
)


class Command(BaseCommand):
    help = "Injecte des donnees de demonstration LabResa."

    def handle(self, *args, **options):
        users_data = [
            ("labrespo", "LABRESPO"),
            ("service3ph", "SERVICE_3PH"),
            ("enseignant1", "ENSEIGNANT"),
            ("enseignant2", "ENSEIGNANT"),
            ("etudiant1", "ETUDIANT"),
            ("etudiant2", "ETUDIANT"),
            ("etudiant3", "ETUDIANT"),
        ]

        created_users = {}
        for username, role in users_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": username.capitalize(),
                    "last_name": "LabResa",
                    "email": f"{username}@labresa.local",
                    "role": role,
                    "departement": "Sciences et Ingenierie",
                    "is_active": True,
                },
            )
            user.role = role
            user.set_password("LabResa123!")
            user.save()
            created_users[username] = user

        groupes = [
            ("GINFO-A1", "Informatique", "Licence 3", "2025-2026", "Vision IA"),
            ("GSE-B2", "Systemes Embarques", "Master 1", "2025-2026", "Robotique labo"),
        ]
        created_groupes = []
        for g in groupes:
            groupe, _ = Groupe.objects.get_or_create(
                nom_groupe=g[0],
                defaults={
                    "filiere": g[1],
                    "niveau": g[2],
                    "annee_universitaire": g[3],
                    "sujet_projet": g[4],
                },
            )
            created_groupes.append(groupe)

        memberships = [
            ("etudiant1", created_groupes[0]),
            ("etudiant2", created_groupes[0]),
            ("etudiant3", created_groupes[1]),
        ]
        for username, groupe in memberships:
            MembreGroupe.objects.get_or_create(
                etudiant=created_users[username],
                groupe=groupe,
            )

        AffectationGroupe.objects.get_or_create(
            groupe=created_groupes[0],
            defaults={
                "enseignant": created_users["enseignant1"],
                "attribue_par": created_users["service3ph"],
            },
        )
        AffectationGroupe.objects.get_or_create(
            groupe=created_groupes[1],
            defaults={
                "enseignant": created_users["enseignant2"],
                "attribue_par": created_users["service3ph"],
            },
        )

        microscope, _ = Materiel.objects.get_or_create(
            nom="Microscope Numerique",
            defaults={
                "description": "Microscope numerique HD pour analyse d'echantillons.",
                "categorie": "Optique",
                "quantite_totale": 10,
                "quantite_disponible": 8,
                "etat_general": Materiel.EtatGeneral.BON,
                "date_achat": timezone.localdate(),
                "seuil_alerte": 2,
            },
        )
        Materiel.objects.get_or_create(
            nom="Carte FPGA",
            defaults={
                "description": "Kit FPGA pour projets electroniques avances.",
                "categorie": "Electronique",
                "quantite_totale": 6,
                "quantite_disponible": 6,
                "etat_general": Materiel.EtatGeneral.NEUF,
                "date_achat": timezone.localdate(),
                "seuil_alerte": 1,
            },
        )

        demande_existante, _ = Demande.objects.get_or_create(
            etudiant=created_users["etudiant1"],
            groupe=created_groupes[0],
            type_demande=Demande.TypeDemande.EXISTANT,
            defaults={
                "statut": Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT,
                "date_souhaitee_retour": timezone.localdate() + timedelta(days=7),
                "motif": "Travaux pratiques de microscopie.",
                "commentaire_enseignant": "",
                "commentaire_labrespo": "",
            },
        )
        LigneDemande.objects.get_or_create(
            demande=demande_existante,
            materiel=microscope,
            defaults={"quantite_demandee": 2, "quantite_validee": 0},
        )

        demande_nouvelle, _ = Demande.objects.get_or_create(
            etudiant=created_users["etudiant3"],
            groupe=created_groupes[1],
            type_demande=Demande.TypeDemande.NOUVEAU,
            defaults={
                "statut": Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT,
                "date_souhaitee_retour": timezone.localdate() + timedelta(days=10),
                "motif": "Projet de vision avancee.",
                "commentaire_enseignant": "",
                "commentaire_labrespo": "",
            },
        )
        DemandeNouveauMateriel.objects.get_or_create(
            demande=demande_nouvelle,
            defaults={
                "nom_materiel_souhaite": "Camera Thermique",
                "description": "Camera thermique haute precision.",
                "categorie_souhaitee": "Vision",
                "justification": "Necessaire pour detection thermique des circuits.",
            },
        )

        self.stdout.write(self.style.SUCCESS("Donnees de demonstration injectees avec succes."))
