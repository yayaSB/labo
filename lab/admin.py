from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AffectationGroupe,
    Demande,
    DemandeNouveauMateriel,
    Groupe,
    LigneDemande,
    Materiel,
    MembreGroupe,
    MouvementStock,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Informations metier", {"fields": ("role", "departement", "date_inscription")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "departement")


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
    list_display = ("id", "etudiant", "groupe", "type_demande", "statut", "date_demande")
    list_filter = ("type_demande", "statut", "date_demande")
    search_fields = ("etudiant__username", "groupe__nom_groupe", "motif")
    inlines = [LigneDemandeInline]


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
