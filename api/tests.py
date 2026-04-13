from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from lab.models import Composant, DemandeWorkflow

User = get_user_model()


class WorkflowAPITests(APITestCase):
    def setUp(self):
        self.encadrant = User.objects.create_user(
            username="enc_test",
            password="LabResa123!",
            role=User.Role.ENCADRANT,
        )
        self.etudiant = User.objects.create_user(
            username="etu_test",
            password="LabResa123!",
            role=User.Role.ETUDIANT,
            encadrant=self.encadrant,
            classe="GI-3A",
        )
        self.etudiant.encadrants.set([self.encadrant])
        self.labo = User.objects.create_user(
            username="labo_test",
            password="LabResa123!",
            role=User.Role.LABRESPO,
        )
        self.composant = Composant.objects.create(
            nom="Capteur test",
            reference="CAP-01",
            quantite_disponible=2,
            seuil_alerte=1,
            localisation="L1",
        )

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_student_can_create_demande(self):
        self._auth(self.etudiant)
        response = self.client.post(
            reverse("api_demande_create"),
            {"composant_id": self.composant.id, "quantite": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["statut"],
            DemandeWorkflow.Statut.EN_ATTENTE_ENCADRANT,
        )

    def test_labo_marks_en_attente_achat_when_stock_insufficient(self):
        demande = DemandeWorkflow.objects.create(
            etudiant=self.etudiant,
            composant=self.composant,
            quantite=5,
            statut=DemandeWorkflow.Statut.EN_ATTENTE_LABO,
        )
        self._auth(self.labo)
        response = self.client.put(
            reverse("api_demande_reserver", kwargs={"demande_id": demande.id}),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        demande.refresh_from_db()
        self.assertEqual(demande.statut, DemandeWorkflow.Statut.EN_ATTENTE_ACHAT)
