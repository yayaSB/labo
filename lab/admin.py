from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.forms import ModelForm

from .models import (
    AffectationGroupe,
    Achat,
    Composant,
    Demande,
    DemandeWorkflow,
    DemandeNouveauMateriel,
    Groupe,
    HistoriqueAction,
    LigneDemande,
    Materiel,
    MembreGroupe,
    MouvementStock,
    Notification,
    User,
)


class CustomUserAdminForm(ModelForm):
    groupes_etudiant = forms.ModelMultipleChoiceField(
        queryset=Groupe.objects.none(),
        required=False,
        label="Groupes etudiant",
        help_text="Selectionnez les groupes de cet etudiant.",
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["encadrants"].queryset = User.objects.filter(role=User.Role.ENCADRANT)
        self.fields["encadrant"].queryset = User.objects.filter(role=User.Role.ENCADRANT)
        self.fields["groupes_etudiant"].queryset = Groupe.objects.order_by("nom_groupe")

        if self.instance and self.instance.pk and self.instance.role == User.Role.ETUDIANT:
            self.fields["groupes_etudiant"].initial = Groupe.objects.filter(
                membres__etudiant=self.instance
            ).distinct()

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        groupes = cleaned.get("groupes_etudiant")
        if role == User.Role.ETUDIANT and not groupes:
            self.add_error(
                "groupes_etudiant",
                "Attribuez au moins un groupe a l'etudiant.",
            )
        return cleaned


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    filter_horizontal = ("groups", "user_permissions", "encadrants")
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "classe",
        "groupes_list",
        "encadrants_list",
        "is_active",
    )
    list_filter = ("role", "is_active", "departement", "classe")

    def get_fieldsets(self, request, obj=None):
        metier_fields = [
            "role",
            "departement",
            "classe",
            "date_inscription",
            "encadrants",
            "groupes_etudiant",
        ]
        return UserAdmin.fieldsets + (
            (
                "Informations metier",
                {"fields": tuple(metier_fields)},
            ),
        )

    @admin.display(description="Groupes")
    def groupes_list(self, obj):
        if obj.role != User.Role.ETUDIANT:
            return "-"
        groupes = Groupe.objects.filter(membres__etudiant=obj).distinct()
        if not groupes.exists():
            return "-"
        return ", ".join(g.nom_groupe for g in groupes)

    @admin.display(description="Encadrants")
    def encadrants_list(self, obj):
        if obj.role != User.Role.ETUDIANT:
            return "-"
        linked = obj.encadrants.all()
        if linked.exists():
            return ", ".join(str(e) for e in linked)
        if obj.encadrant_id:
            return str(obj.encadrant)
        return "-"

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        user = form.instance
        if user.role != User.Role.ETUDIANT:
            user.encadrants.clear()
            MembreGroupe.objects.filter(etudiant=user).delete()
            if user.encadrant_id:
                user.encadrant = None
                user.save(update_fields=["encadrant"])
            return

        selected_groupes = form.cleaned_data.get("groupes_etudiant")
        selected_ids = set(selected_groupes.values_list("id", flat=True)) if selected_groupes else set()
        existing_ids = set(
            MembreGroupe.objects.filter(etudiant=user).values_list("groupe_id", flat=True)
        )

        remove_ids = existing_ids - selected_ids
        add_ids = selected_ids - existing_ids
        if remove_ids:
            MembreGroupe.objects.filter(etudiant=user, groupe_id__in=remove_ids).delete()
        for groupe_id in add_ids:
            MembreGroupe.objects.create(etudiant=user, groupe_id=groupe_id)

        selected = user.encadrants.order_by("id")
        first = selected.first()
        if first and user.encadrant_id != first.id:
            user.encadrant = first
            user.save(update_fields=["encadrant"])
        elif not first and user.encadrant_id:
            user.encadrants.add(user.encadrant)

    class Media:
        js = ("admin/js/user_role_toggle.js",)


@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ("nom_groupe", "filiere", "niveau", "annee_universitaire")
    search_fields = ("nom_groupe", "filiere", "niveau")


@admin.register(MembreGroupe)
class MembreGroupeAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "groupe")
    list_filter = ("groupe",)
    search_fields = ("etudiant__username", "etudiant__first_name", "etudiant__last_name")


@admin.register(AffectationGroupe)
class AffectationGroupeAdmin(admin.ModelAdmin):
    list_display = ("groupe", "enseignant", "attribue_par", "date_affectation")
    list_filter = ("date_affectation",)
    search_fields = ("groupe__nom_groupe", "enseignant__username", "attribue_par__username")


class LigneDemandeInline(admin.TabularInline):
    model = LigneDemande
    extra = 0


@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "etudiant",
        "groupe",
        "type_demande",
        "statut",
        "statut_humain",
        "date_demande",
    )
    list_filter = ("type_demande", "statut", "date_demande")
    search_fields = ("etudiant__username", "groupe__nom_groupe", "motif")
    inlines = [LigneDemandeInline]

    @admin.display(description="Libelle statut")
    def statut_humain(self, obj):
        return obj.statut_message


@admin.register(DemandeNouveauMateriel)
class DemandeNouveauMaterielAdmin(admin.ModelAdmin):
    list_display = ("demande", "nom_materiel_souhaite", "categorie_souhaitee")
    search_fields = ("nom_materiel_souhaite", "categorie_souhaitee")


@admin.register(Materiel)
class MaterielAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "categorie",
        "quantite_disponible",
        "quantite_totale",
        "etat_general",
        "seuil_alerte",
    )
    list_filter = ("categorie", "etat_general")
    search_fields = ("nom", "categorie")


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("materiel", "demande", "type_mouvement", "quantite", "date_mouvement")
    list_filter = ("type_mouvement", "date_mouvement")
    search_fields = ("materiel__nom", "demande__id")


@admin.register(Composant)
class ComposantAdmin(admin.ModelAdmin):
    list_display = ("nom", "reference", "quantite_disponible", "seuil_alerte", "localisation")
    list_filter = ("localisation",)
    search_fields = ("nom", "reference")


@admin.register(DemandeWorkflow)
class DemandeWorkflowAdmin(admin.ModelAdmin):
    list_display = ("id", "etudiant", "composant", "quantite", "statut", "date_demande")
    list_filter = ("statut", "date_demande")
    search_fields = ("etudiant__username", "composant__reference", "composant__nom")


@admin.register(Achat)
class AchatAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "demande",
        "composant",
        "quantite_achetee",
        "fournisseur",
        "statut",
        "date_commande",
    )
    list_filter = ("statut", "date_commande")
    search_fields = ("composant__reference", "fournisseur")


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(admin.ModelAdmin):
    list_display = ("demande", "action", "acteur", "date_action")
    list_filter = ("date_action",)
    search_fields = ("action", "demande__id", "acteur__username")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "message")
