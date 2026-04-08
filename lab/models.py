from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ETUDIANT = "ETUDIANT", "Etudiant"
        ENSEIGNANT = "ENSEIGNANT", "Enseignant"
        LABRESPO = "LABRESPO", "LabRespo"
        SERVICE_3PH = "SERVICE_3PH", "Service 3PH"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.SERVICE_3PH
    )
    departement = models.CharField(max_length=120, blank=True)
    date_inscription = models.DateTimeField(default=timezone.now)

    def __str__(self):
        full_name = self.get_full_name().strip()
        return full_name if full_name else self.username


class Groupe(models.Model):
    nom_groupe = models.CharField(max_length=120, unique=True)
    filiere = models.CharField(max_length=120)
    niveau = models.CharField(max_length=60)
    annee_universitaire = models.CharField(max_length=20)
    sujet_projet = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["nom_groupe"]

    def __str__(self):
        return f"{self.nom_groupe} - {self.filiere} {self.niveau}"


class MembreGroupe(models.Model):
    etudiant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="membreships"
    )
    groupe = models.ForeignKey(Groupe, on_delete=models.CASCADE, related_name="membres")

    class Meta:
        unique_together = ("etudiant", "groupe")
        verbose_name = "Membre de groupe"
        verbose_name_plural = "Membres de groupes"

    def clean(self):
        if self.etudiant.role != User.Role.ETUDIANT:
            raise ValidationError("Seuls les utilisateurs ETUDIANT peuvent etre membres.")

    def __str__(self):
        return f"{self.etudiant} -> {self.groupe.nom_groupe}"


class AffectationGroupe(models.Model):
    groupe = models.OneToOneField(
        Groupe, on_delete=models.CASCADE, related_name="affectation"
    )
    enseignant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="groupes_assignes"
    )
    attribue_par = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="affectations_creees"
    )
    date_affectation = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date_affectation"]
        verbose_name = "Affectation groupe"
        verbose_name_plural = "Affectations groupes"

    def clean(self):
        if self.enseignant.role != User.Role.ENSEIGNANT:
            raise ValidationError("Le destinataire doit etre un ENSEIGNANT.")
        if self.attribue_par.role != User.Role.SERVICE_3PH:
            raise ValidationError("L'attribution doit etre faite par SERVICE_3PH.")

    def __str__(self):
        return f"{self.groupe.nom_groupe} -> {self.enseignant}"


class Materiel(models.Model):
    class EtatGeneral(models.TextChoices):
        NEUF = "NEUF", "Neuf"
        BON = "BON", "Bon"
        PANNE = "PANNE", "Panne"
        MAINTENANCE = "MAINTENANCE", "Maintenance"

    nom = models.CharField(max_length=180, unique=True)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=120)
    quantite_totale = models.PositiveIntegerField(default=0)
    quantite_disponible = models.PositiveIntegerField(default=0)
    etat_general = models.CharField(
        max_length=20, choices=EtatGeneral.choices, default=EtatGeneral.BON
    )
    image = models.ImageField(upload_to="materials/", blank=True, null=True)
    date_achat = models.DateField(blank=True, null=True)
    seuil_alerte = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["nom"]

    def clean(self):
        if self.quantite_disponible > self.quantite_totale:
            raise ValidationError(
                "La quantite disponible ne peut pas depasser la quantite totale."
            )

    @property
    def stock_faible(self):
        return self.quantite_disponible <= self.seuil_alerte

    def __str__(self):
        return f"{self.nom} ({self.quantite_disponible}/{self.quantite_totale})"


class Demande(models.Model):
    class TypeDemande(models.TextChoices):
        EXISTANT = "EXISTANT", "Materiel existant"
        NOUVEAU = "NOUVEAU", "Nouveau materiel"

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        COMMENTEE = "COMMENTEE", "Commentee enseignant"
        VALIDEE = "VALIDEE", "Validee"
        REFUSEE = "REFUSEE", "Refusee"
        EN_COURS = "EN_COURS", "Materiel sorti"
        RETOURNEE = "RETOURNEE", "Retournee"

    etudiant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="demandes_etudiant"
    )
    groupe = models.ForeignKey(Groupe, on_delete=models.PROTECT, related_name="demandes")
    type_demande = models.CharField(max_length=10, choices=TypeDemande.choices)
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    date_demande = models.DateTimeField(default=timezone.now)
    date_souhaitee_retour = models.DateField()
    motif = models.TextField()
    commentaire_enseignant = models.TextField(blank=True)
    commentaire_labrespo = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_demande"]

    def clean(self):
        if self.etudiant.role != User.Role.ETUDIANT:
            raise ValidationError("La demande doit etre creee par un ETUDIANT.")

    @property
    def en_retard(self):
        return self.statut == self.Statut.EN_COURS and self.date_souhaitee_retour < timezone.localdate()

    def __str__(self):
        return f"Demande #{self.pk} - {self.etudiant} - {self.get_type_demande_display()}"


class LigneDemande(models.Model):
    demande = models.ForeignKey(
        Demande, on_delete=models.CASCADE, related_name="lignes_demande"
    )
    materiel = models.ForeignKey(Materiel, on_delete=models.PROTECT, related_name="lignes")
    quantite_demandee = models.PositiveIntegerField()
    quantite_validee = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("demande", "materiel")

    def clean(self):
        if self.quantite_validee > self.quantite_demandee:
            raise ValidationError("La quantite validee ne peut depasser la demande.")

    def __str__(self):
        return f"{self.materiel.nom} x{self.quantite_demandee}"


class DemandeNouveauMateriel(models.Model):
    demande = models.OneToOneField(
        Demande, on_delete=models.CASCADE, related_name="nouveau_materiel"
    )
    nom_materiel_souhaite = models.CharField(max_length=180)
    description = models.TextField()
    categorie_souhaitee = models.CharField(max_length=120)
    justification = models.TextField()

    def __str__(self):
        return f"Nouveau: {self.nom_materiel_souhaite}"


class MouvementStock(models.Model):
    class TypeMouvement(models.TextChoices):
        SORTIE = "SORTIE", "Sortie"
        RETOUR = "RETOUR", "Retour"

    materiel = models.ForeignKey(
        Materiel, on_delete=models.PROTECT, related_name="mouvements"
    )
    demande = models.ForeignKey(
        Demande, on_delete=models.CASCADE, related_name="mouvements"
    )
    type_mouvement = models.CharField(max_length=10, choices=TypeMouvement.choices)
    quantite = models.PositiveIntegerField()
    date_mouvement = models.DateTimeField(default=timezone.now)
    valide_par = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="mouvements_valides"
    )

    class Meta:
        ordering = ["-date_mouvement"]

    def __str__(self):
        return f"{self.get_type_mouvement_display()} {self.materiel.nom} ({self.quantite})"
