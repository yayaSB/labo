import csv
import io

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from lab.models import Achat, Composant, DemandeWorkflow, Notification

from .serializers import (
    AchatCreateSerializer,
    AchatSerializer,
    ComposantSerializer,
    DemandeCreateSerializer,
    DemandeWorkflowSerializer,
    EncadrantAdminSerializer,
    EncadrantDecisionSerializer,
    LoginSerializer,
    NotificationSerializer,
    StudentAdminSerializer,
    UserMeSerializer,
)
from .services import log_history, notify_role_users, notify_user

User = get_user_model()


def _forbidden_role_response():
    return Response({"detail": "Role non autorise."}, status=status.HTTP_403_FORBIDDEN)


def _is_role(user, *roles):
    return user.is_authenticated and user.has_api_role(*roles)


def _student_has_encadrant(student, encadrant):
    if student.encadrants.filter(id=encadrant.id).exists():
        return True
    return student.encadrant_id == encadrant.id


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            user_by_email = User.objects.filter(email__iexact=identifier).first()
            if user_by_email:
                user = authenticate(
                    request,
                    username=user_by_email.username,
                    password=password,
                )
        if user is None or not user.is_active:
            return Response(
                {"detail": "Identifiants invalides."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserMeSerializer(user).data,
            }
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "refresh requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Token invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Deconnexion reussie."})


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserMeSerializer(request.user).data)


class NotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)[:50]
        return Response(NotificationSerializer(notifications, many=True).data)


class NotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, notification_id):
        notification = Notification.objects.filter(
            id=notification_id,
            user=request.user,
        ).first()
        if not notification:
            return Response(
                {"detail": "Notification introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"detail": "Notification lue."})


class ComposantListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        composants = Composant.objects.all()
        return Response(ComposantSerializer(composants, many=True).data)

    def post(self, request):
        if not _is_role(request.user, "labo", "admin"):
            return _forbidden_role_response()
        serializer = ComposantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        composant = serializer.save()
        return Response(ComposantSerializer(composant).data, status=status.HTTP_201_CREATED)


class ComposantUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, composant_id):
        if not _is_role(request.user, "labo", "admin"):
            return _forbidden_role_response()
        composant = Composant.objects.filter(id=composant_id).first()
        if not composant:
            return Response(
                {"detail": "Composant introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ComposantSerializer(composant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StudentDemandeCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _is_role(request.user, "etudiant"):
            return _forbidden_role_response()
        serializer = DemandeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        composant = Composant.objects.get(id=serializer.validated_data["composant_id"])
        demande = DemandeWorkflow.objects.create(
            etudiant=request.user,
            composant=composant,
            quantite=serializer.validated_data["quantite"],
            statut=DemandeWorkflow.Statut.EN_ATTENTE_ENCADRANT,
        )
        log_history(demande, "Creation demande par etudiant", request.user)

        for encadrant in request.user.get_encadrants():
            notify_user(
                encadrant,
                f"Nouvelle demande #{demande.id} en attente de validation.",
            )

        return Response(DemandeWorkflowSerializer(demande).data, status=status.HTTP_201_CREATED)


class StudentMesDemandesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "etudiant"):
            return _forbidden_role_response()
        demandes = DemandeWorkflow.objects.filter(etudiant=request.user)
        return Response(DemandeWorkflowSerializer(demandes, many=True).data)


class StudentDemandeDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, demande_id):
        if not _is_role(request.user, "etudiant"):
            return _forbidden_role_response()

        demande = DemandeWorkflow.objects.filter(id=demande_id, etudiant=request.user).first()
        if not demande:
            return Response({"detail": "Demande introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if not demande.can_cancel_by_student:
            return Response(
                {"detail": "Annulation impossible apres validation encadrant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        demande_id_val = demande.id
        demande.delete()
        return Response({"detail": f"Demande #{demande_id_val} annulee."})


class EncadrantDemandesClasseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "encadrant"):
            return _forbidden_role_response()

        demandes = DemandeWorkflow.objects.filter(
            Q(etudiant__encadrants=request.user) | Q(etudiant__encadrant=request.user)
        ).distinct()
        return Response(DemandeWorkflowSerializer(demandes, many=True).data)


class EncadrantValiderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, demande_id):
        if not _is_role(request.user, "encadrant"):
            return _forbidden_role_response()
        serializer = EncadrantDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        demande = DemandeWorkflow.objects.filter(id=demande_id).select_related("etudiant").first()
        if not demande:
            return Response({"detail": "Demande introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if not _student_has_encadrant(demande.etudiant, request.user):
            return _forbidden_role_response()
        if demande.statut != DemandeWorkflow.Statut.EN_ATTENTE_ENCADRANT:
            return Response(
                {"detail": "Demande deja traitee par encadrant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demande.statut = DemandeWorkflow.Statut.EN_ATTENTE_LABO
        demande.commentaire_encadrant = serializer.validated_data.get("commentaire_encadrant", "")
        demande.save(update_fields=["statut", "commentaire_encadrant", "date_derniere_maj"])
        log_history(demande, "Validation encadrant", request.user)
        notify_user(demande.etudiant, f"Votre demande #{demande.id} est validee par encadrant.")
        notify_role_users(
            [User.Role.LABRESPO],
            f"Demande #{demande.id} en attente labo.",
        )
        return Response(DemandeWorkflowSerializer(demande).data)


class EncadrantRefuserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, demande_id):
        if not _is_role(request.user, "encadrant"):
            return _forbidden_role_response()
        serializer = EncadrantDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        demande = DemandeWorkflow.objects.filter(id=demande_id).select_related("etudiant").first()
        if not demande:
            return Response({"detail": "Demande introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if not _student_has_encadrant(demande.etudiant, request.user):
            return _forbidden_role_response()
        if demande.statut != DemandeWorkflow.Statut.EN_ATTENTE_ENCADRANT:
            return Response(
                {"detail": "Demande deja traitee par encadrant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demande.statut = DemandeWorkflow.Statut.REFUSEE
        demande.commentaire_encadrant = serializer.validated_data.get("commentaire_encadrant", "")
        demande.save(update_fields=["statut", "commentaire_encadrant", "date_derniere_maj"])
        log_history(demande, "Refus encadrant", request.user)
        notify_user(demande.etudiant, f"Votre demande #{demande.id} a ete refusee.")
        return Response(DemandeWorkflowSerializer(demande).data)


class LaboDemandesAttenteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "labo"):
            return _forbidden_role_response()
        demandes = DemandeWorkflow.objects.filter(statut=DemandeWorkflow.Statut.EN_ATTENTE_LABO)
        return Response(DemandeWorkflowSerializer(demandes, many=True).data)


class LaboReserverAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, demande_id):
        if not _is_role(request.user, "labo"):
            return _forbidden_role_response()

        demande = DemandeWorkflow.objects.select_related("composant", "etudiant").filter(id=demande_id).first()
        if not demande:
            return Response({"detail": "Demande introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if demande.statut != DemandeWorkflow.Statut.EN_ATTENTE_LABO:
            return Response(
                {"detail": "Demande non eligible pour reservation labo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            composant = demande.composant
            if composant.quantite_disponible >= demande.quantite:
                composant.quantite_disponible -= demande.quantite
                composant.save(update_fields=["quantite_disponible", "updated_at"])
                demande.statut = DemandeWorkflow.Statut.APPROUVEE
                demande.save(update_fields=["statut", "date_derniere_maj"])
                log_history(demande, "Reservation approuvee par labo", request.user)
                notify_user(
                    demande.etudiant,
                    f"Demande #{demande.id} approuvee. Materiel disponible au labo.",
                )
            else:
                demande.statut = DemandeWorkflow.Statut.EN_ATTENTE_ACHAT
                demande.save(update_fields=["statut", "date_derniere_maj"])
                log_history(demande, "Stock insuffisant, en attente achat", request.user)
                notify_role_users(
                    [User.Role.SERVICE_ACHAT],
                    f"Demande #{demande.id} en attente achat.",
                )

        return Response(DemandeWorkflowSerializer(demande).data)


class AchatDemandesAttenteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "achat"):
            return _forbidden_role_response()
        demandes = DemandeWorkflow.objects.filter(statut=DemandeWorkflow.Statut.EN_ATTENTE_ACHAT)
        return Response(DemandeWorkflowSerializer(demandes, many=True).data)


class AchatCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "achat"):
            return _forbidden_role_response()
        achats = Achat.objects.all()
        return Response(AchatSerializer(achats, many=True).data)

    def post(self, request):
        if not _is_role(request.user, "achat"):
            return _forbidden_role_response()
        serializer = AchatCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        demande = DemandeWorkflow.objects.select_related("composant").filter(
            id=serializer.validated_data["demande_id"]
        ).first()
        if not demande:
            return Response({"detail": "Demande introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if demande.statut != DemandeWorkflow.Statut.EN_ATTENTE_ACHAT:
            return Response(
                {"detail": "La demande n'est pas en attente achat."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        achat = Achat.objects.create(
            demande=demande,
            composant=demande.composant,
            quantite_achetee=serializer.validated_data["quantite_achetee"],
            fournisseur=serializer.validated_data["fournisseur"],
            statut=Achat.Statut.EN_COURS,
        )
        log_history(demande, f"Achat cree (commande #{achat.id})", request.user)
        return Response(AchatSerializer(achat).data, status=status.HTTP_201_CREATED)


class AchatReceptionnerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, achat_id):
        if not _is_role(request.user, "achat"):
            return _forbidden_role_response()

        achat = Achat.objects.select_related("composant", "demande").filter(id=achat_id).first()
        if not achat:
            return Response({"detail": "Achat introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if achat.statut == Achat.Statut.RECU:
            return Response({"detail": "Achat deja receptionne."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            achat.statut = Achat.Statut.RECU
            achat.date_reception = timezone.now()
            achat.save(update_fields=["statut", "date_reception"])

            composant = achat.composant
            composant.quantite_disponible += achat.quantite_achetee
            composant.save(update_fields=["quantite_disponible", "updated_at"])

            demande = achat.demande
            demande.statut = DemandeWorkflow.Statut.EN_ATTENTE_LABO
            demande.save(update_fields=["statut", "date_derniere_maj"])
            log_history(demande, f"Achat #{achat.id} receptionne", request.user)
            notify_role_users(
                [User.Role.LABRESPO],
                f"Achat receptionne pour la demande #{demande.id}. Retour en attente labo.",
            )

        return Response(AchatSerializer(achat).data)


class EncadrantAdminListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        encadrants = User.objects.filter(role=User.Role.ENCADRANT)
        return Response(EncadrantAdminSerializer(encadrants, many=True).data)

    def post(self, request):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        serializer = EncadrantAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(EncadrantAdminSerializer(user).data, status=status.HTTP_201_CREATED)


class EncadrantAdminDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, encadrant_id):
        return User.objects.filter(id=encadrant_id, role=User.Role.ENCADRANT).first()

    def get(self, request, encadrant_id):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        user = self.get_object(encadrant_id)
        if not user:
            return Response({"detail": "Encadrant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EncadrantAdminSerializer(user).data)

    def put(self, request, encadrant_id):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        user = self.get_object(encadrant_id)
        if not user:
            return Response({"detail": "Encadrant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EncadrantAdminSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(EncadrantAdminSerializer(user).data)

    def delete(self, request, encadrant_id):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        user = self.get_object(encadrant_id)
        if not user:
            return Response({"detail": "Encadrant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudentAdminListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        students = User.objects.filter(role=User.Role.ETUDIANT)
        return Response(StudentAdminSerializer(students, many=True).data)

    def post(self, request):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        serializer = StudentAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(StudentAdminSerializer(student).data, status=status.HTTP_201_CREATED)


class StudentAdminDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, student_id):
        return User.objects.filter(id=student_id, role=User.Role.ETUDIANT).first()

    def get(self, request, student_id):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        student = self.get_object(student_id)
        if not student:
            return Response({"detail": "Etudiant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(StudentAdminSerializer(student).data)

    def put(self, request, student_id):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        student = self.get_object(student_id)
        if not student:
            return Response({"detail": "Etudiant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentAdminSerializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(StudentAdminSerializer(student).data)

    def delete(self, request, student_id):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()
        student = self.get_object(student_id)
        if not student:
            return Response({"detail": "Etudiant introuvable."}, status=status.HTTP_404_NOT_FOUND)
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StatistiquesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()

        demandes_by_status = list(
            DemandeWorkflow.objects.values("statut").annotate(total=Count("id")).order_by("statut")
        )

        average_duration = DemandeWorkflow.objects.filter(
            statut=DemandeWorkflow.Statut.TERMINEE
        ).aggregate(
            avg_delay=Avg(
                ExpressionWrapper(
                    F("date_derniere_maj") - F("date_demande"),
                    output_field=DurationField(),
                )
            )
        )["avg_delay"]
        avg_delay_hours = (
            round(average_duration.total_seconds() / 3600, 2)
            if average_duration is not None
            else 0
        )

        top_components = list(
            DemandeWorkflow.objects.values("composant__nom", "composant__reference")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        refusal_rates = []
        encadrants = User.objects.filter(role=User.Role.ENCADRANT)
        for encadrant in encadrants:
            qs = DemandeWorkflow.objects.filter(
                Q(etudiant__encadrants=encadrant) | Q(etudiant__encadrant=encadrant)
            ).distinct()
            total = qs.count()
            refused = qs.filter(statut=DemandeWorkflow.Statut.REFUSEE).count()
            rate = round((refused / total) * 100, 2) if total else 0
            refusal_rates.append(
                {
                    "encadrant_id": encadrant.id,
                    "encadrant": encadrant.get_full_name() or encadrant.username,
                    "total_demandes": total,
                    "demandes_refusees": refused,
                    "taux_refus": rate,
                }
            )

        return Response(
            {
                "demandes_par_statut": demandes_by_status,
                "delai_moyen_traitement_heures": avg_delay_hours,
                "top_5_composants": top_components,
                "taux_refus_par_encadrant": refusal_rates,
            }
        )


class RapportsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_role(request.user, "admin"):
            return _forbidden_role_response()

        format_type = request.query_params.get("format", "csv").lower()
        demandes = DemandeWorkflow.objects.select_related("etudiant", "composant").all()

        if format_type == "pdf":
            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            y = height - 40
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, "Rapport LabResa - Demandes")
            y -= 25
            pdf.setFont("Helvetica", 9)
            for demande in demandes:
                line = (
                    f"#{demande.id} | {demande.etudiant.username} | {demande.composant.reference} "
                    f"| qte={demande.quantite} | {demande.statut} | {demande.date_demande:%Y-%m-%d}"
                )
                pdf.drawString(40, y, line[:120])
                y -= 14
                if y < 40:
                    pdf.showPage()
                    y = height - 40
                    pdf.setFont("Helvetica", 9)
            pdf.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=labresa_rapport.pdf"
            return response

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=labresa_rapport.csv"
        writer = csv.writer(response)
        writer.writerow(
            [
                "id_demande",
                "etudiant",
                "composant",
                "reference",
                "quantite",
                "statut",
                "date_demande",
            ]
        )
        for demande in demandes:
            writer.writerow(
                [
                    demande.id,
                    demande.etudiant.username,
                    demande.composant.nom,
                    demande.composant.reference,
                    demande.quantite,
                    demande.statut,
                    demande.date_demande.isoformat(),
                ]
            )
        return response
