from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory

from .models import (
    AffectationGroupe,
    Demande,
    DemandeNouveauMateriel,
    Groupe,
    LigneDemande,
    Materiel,
    User,
)


class DateInput(forms.DateInput):
    input_type = "date"


class LabResaAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "departement", "classe"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "departement": forms.TextInput(attrs={"class": "form-control"}),
            "classe": forms.TextInput(attrs={"class": "form-control"}),
        }


class MaterielForm(forms.ModelForm):
    class Meta:
        model = Materiel
        fields = [
            "nom",
            "description",
            "categorie",
            "quantite_totale",
            "quantite_disponible",
            "etat_general",
            "image",
            "date_achat",
            "seuil_alerte",
        ]
        widgets = {"date_achat": DateInput()}


class DemandeExistantForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ["groupe", "date_souhaitee_retour", "motif"]
        widgets = {"date_souhaitee_retour": DateInput()}

    def __init__(self, *args, **kwargs):
        etudiant = kwargs.pop("etudiant")
        super().__init__(*args, **kwargs)
        groupes_ids = etudiant.membreships.values_list("groupe_id", flat=True)
        self.fields["groupe"].queryset = Groupe.objects.filter(id__in=groupes_ids)


class LigneDemandeForm(forms.ModelForm):
    class Meta:
        model = LigneDemande
        fields = ["materiel", "quantite_demandee"]


LigneDemandeFormSet = inlineformset_factory(
    Demande,
    LigneDemande,
    form=LigneDemandeForm,
    extra=2,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class DemandeNouveauMaterielForm(forms.ModelForm):
    class Meta:
        model = DemandeNouveauMateriel
        fields = [
            "nom_materiel_souhaite",
            "description",
            "categorie_souhaitee",
            "justification",
        ]


class DemandeNouveauParentForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ["groupe", "date_souhaitee_retour", "motif"]
        widgets = {"date_souhaitee_retour": DateInput()}

    def __init__(self, *args, **kwargs):
        etudiant = kwargs.pop("etudiant")
        super().__init__(*args, **kwargs)
        groupes_ids = etudiant.membreships.values_list("groupe_id", flat=True)
        self.fields["groupe"].queryset = Groupe.objects.filter(id__in=groupes_ids)


class TeacherDecisionForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ["statut", "commentaire_enseignant"]
        widgets = {
            "commentaire_enseignant": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Commentaire / recommandation"}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["statut"].choices = [
            (
                Demande.Statut.VALIDEE_PAR_ENSEIGNANT,
                "Valider pedagogiquement",
            ),
            (
                Demande.Statut.REFUSEE,
                "Refuser pedagogiquement",
            ),
        ]


class LabRespoDecisionForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ["statut", "commentaire_labrespo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["statut"].choices = [
            (Demande.Statut.EN_COURS_TRAITEMENT, "Mettre en cours de traitement"),
            (Demande.Statut.EN_PAUSE, "Mettre en pause"),
            (Demande.Statut.ENVOYEE_SERVICE_ACHAT, "Envoyer au service achat"),
            (Demande.Statut.DISPONIBLE, "Marquer disponible"),
            (Demande.Statut.RETIREE, "Marquer retiree"),
            (Demande.Statut.REFUSEE, "Refuser"),
            (Demande.Statut.TERMINEE, "Terminer"),
        ]


class ServiceAchatDecisionForm(forms.ModelForm):
    class Meta:
        model = Demande
        fields = ["statut"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["statut"].choices = [
            (
                Demande.Statut.ACHAT_EN_COURS_TRAITEMENT,
                "Mettre en cours de traitement achat",
            ),
            (
                Demande.Statut.ACHAT_EN_COURS_LIVRAISON,
                "Mettre en cours de livraison",
            ),
            (
                Demande.Statut.MATERIEL_RECU_AU_LABO,
                "Marquer materiel recu au labo",
            ),
        ]


class AffectationGroupeForm(forms.ModelForm):
    class Meta:
        model = AffectationGroupe
        fields = ["groupe", "enseignant"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["enseignant"].queryset = User.objects.filter(role=User.Role.ENCADRANT)
