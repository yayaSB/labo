from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ETUDIANT = "ETUDIANT", "Etudiant"
        ENCADRANT = "ENCADRANT", "Encadrant"
        LABRESPO = "LABRESPO", "LabRespo"
        SERVICE_ACHAT = "SERVICE_ACHAT", "Service Achat"
        SERVICE_3PH = "SERVICE_3PH", "Service 3PH"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.SERVICE_3PH
    )
    departement = models.CharField(max_length=120, blank=True)
    classe = models.CharField(max_length=60, blank=True)
    encadrant = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="etudiants_encadres",
    )
    date_inscription = models.DateTimeField(default=timezone.now)

    def __str__(self):
        full_name = self.get_full_name().strip()
        return full_name if full_name else self.username

    @property
    def role_api(self):
        mapping = {
            self.Role.ETUDIANT: "etudiant",
            self.Role.ENCADRANT: "encadrant",
            self.Role.LABRESPO: "labo",
            self.Role.SERVICE_ACHAT: "achat",
            self.Role.SERVICE_3PH: "admin",
        }
        return mapping.get(self.role, "")

    def has_api_role(self, *roles):
        return self.role_api in roles


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
        if self.enseignant_id and self.enseignant.role != User.Role.ENCADRANT:
            raise ValidationError("Le destinataire doit etre un ENCADRANT.")
        if self.attribue_par_id and self.attribue_par.role != User.Role.SERVICE_3PH:
            raise ValidationError("L'attribution doit etre faite par SERVICE_3PH.")

    def __str__(self):
        groupe_label = self.groupe.nom_groupe if self.groupe_id else "Groupe non defini"
        enseignant_label = str(self.enseignant) if self.enseignant_id else "Enseignant non defini"
        return f"{groupe_label} -> {enseignant_label}"


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
        EN_ATTENTE_VALIDATION_ENSEIGNANT = (
            "EN_ATTENTE_VALIDATION_ENSEIGNANT",
            "En attente de validation encadrant",
        )
        VALIDEE_PAR_ENSEIGNANT = (
            "VALIDEE_PAR_ENSEIGNANT",
            "Validee par encadrant",
        )
        EN_COURS_TRAITEMENT = "EN_COURS_TRAITEMENT", "En cours de traitement"
        EN_PAUSE = "EN_PAUSE", "En pause"
        ENVOYEE_SERVICE_ACHAT = "ENVOYEE_SERVICE_ACHAT", "Envoyee au service achat"
        ACHAT_EN_COURS_TRAITEMENT = (
            "ACHAT_EN_COURS_TRAITEMENT",
            "Achat en cours de traitement",
        )
        ACHAT_EN_COURS_LIVRAISON = (
            "ACHAT_EN_COURS_LIVRAISON",
            "Achat en cours de livraison",
        )
        MATERIEL_RECU_AU_LABO = (
            "MATERIEL_RECU_AU_LABO",
            "Materiel recu au laboratoire",
        )
        DISPONIBLE = "DISPONIBLE", "Disponible"
        REFUSEE = "REFUSEE", "Refusee"
        RETIREE = "RETIREE", "Retiree"
        TERMINEE = "TERMINEE", "Terminee"

    STATUTS_ACHAT = {
        Statut.ENVOYEE_SERVICE_ACHAT,
        Statut.ACHAT_EN_COURS_TRAITEMENT,
        Statut.ACHAT_EN_COURS_LIVRAISON,
        Statut.MATERIEL_RECU_AU_LABO,
    }

    etudiant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="demandes_etudiant"
    )
    groupe = models.ForeignKey(Groupe, on_delete=models.PROTECT, related_name="demandes")
    type_demande = models.CharField(max_length=10, choices=TypeDemande.choices)
    statut = models.CharField(
        max_length=40,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT,
    )
    date_demande = models.DateTimeField(default=timezone.now)
    date_souhaitee_retour = models.DateField()
    motif = models.TextField()
    commentaire_enseignant = models.TextField(blank=True)
    commentaire_labrespo = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_demande"]

    def clean(self):
        if not self.etudiant_id:
            return
        if self.etudiant.role != User.Role.ETUDIANT:
            raise ValidationError("La demande doit etre creee par un ETUDIANT.")

    @property
    def statut_message(self):
        messages = {
            self.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT: "En attente de validation de votre encadrant",
            self.Statut.VALIDEE_PAR_ENSEIGNANT: "Validee par votre encadrant",
            self.Statut.EN_COURS_TRAITEMENT: "En cours de traitement par le laboratoire",
            self.Statut.EN_PAUSE: "Mise en pause par le laboratoire",
            self.Statut.ENVOYEE_SERVICE_ACHAT: "Votre demande a ete envoyee au service achat",
            self.Statut.ACHAT_EN_COURS_TRAITEMENT: "Le service achat traite votre demande",
            self.Statut.ACHAT_EN_COURS_LIVRAISON: "Le materiel est en cours de livraison",
            self.Statut.MATERIEL_RECU_AU_LABO: "Le materiel a ete recu au laboratoire",
            self.Statut.DISPONIBLE: "Votre materiel est disponible",
            self.Statut.REFUSEE: "Votre demande a ete refusee",
            self.Statut.RETIREE: "Materiel retire, en attente de cloture",
            self.Statut.TERMINEE: "Demande terminee",
        }
        return messages.get(self.statut, self.get_statut_display())

    @property
    def statut_badge_class(self):
        styles = {
            self.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT: "bg-warning text-dark",
            self.Statut.VALIDEE_PAR_ENSEIGNANT: "bg-info text-dark",
            self.Statut.EN_COURS_TRAITEMENT: "bg-primary",
            self.Statut.EN_PAUSE: "bg-secondary",
            self.Statut.ENVOYEE_SERVICE_ACHAT: "bg-warning text-dark",
            self.Statut.ACHAT_EN_COURS_TRAITEMENT: "bg-primary",
            self.Statut.ACHAT_EN_COURS_LIVRAISON: "bg-info text-dark",
            self.Statut.MATERIEL_RECU_AU_LABO: "bg-success",
            self.Statut.DISPONIBLE: "bg-success",
            self.Statut.REFUSEE: "bg-danger",
            self.Statut.RETIREE: "bg-dark",
            self.Statut.TERMINEE: "bg-success",
        }
        return styles.get(self.statut, "bg-secondary")

    @property
    def en_retard(self):
        active_statuses = [
            self.Statut.EN_COURS_TRAITEMENT,
            self.Statut.EN_PAUSE,
            self.Statut.ENVOYEE_SERVICE_ACHAT,
            self.Statut.ACHAT_EN_COURS_TRAITEMENT,
            self.Statut.ACHAT_EN_COURS_LIVRAISON,
            self.Statut.MATERIEL_RECU_AU_LABO,
            self.Statut.DISPONIBLE,
            self.Statut.RETIREE,
        ]
        return self.statut in active_statuses and self.date_souhaitee_retour < timezone.localdate()

    def __str__(self):
        etudiant_label = str(self.etudiant) if self.etudiant_id else "Etudiant non defini"
        type_label = (
            self.get_type_demande_display() if self.type_demande else "Type non defini"
        )
        return f"Demande #{self.pk or 'new'} - {etudiant_label} - {type_label}"


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


class Composant(models.Model):
    nom = models.CharField(max_length=180)
    reference = models.CharField(max_length=80, unique=True)
    quantite_disponible = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=0)
    localisation = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]
        db_table = "composants"

    def __str__(self):
        return f"{self.nom} ({self.reference})"


class DemandeWorkflow(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE_ENCADRANT = "en_attente_encadrant", "En attente encadrant"
        EN_ATTENTE_LABO = "en_attente_labo", "En attente labo"
        EN_ATTENTE_ACHAT = "en_attente_achat", "En attente achat"
        APPROUVEE = "approuvee", "Approuvee"
        REFUSEE = "refusee", "Refusee"
        TERMINEE = "terminee", "Terminee"

    etudiant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workflow_demandes",
    )
    composant = models.ForeignKey(
        Composant,
        on_delete=models.PROTECT,
        related_name="demandes",
    )
    quantite = models.PositiveIntegerField()
    statut = models.CharField(
        max_length=30,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE_ENCADRANT,
    )
    date_demande = models.DateTimeField(default=timezone.now)
    commentaire_encadrant = models.TextField(blank=True)
    date_derniere_maj = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_demande"]
        db_table = "demandes"

    def clean(self):
        if self.etudiant_id and not self.etudiant.has_api_role("etudiant"):
            raise ValidationError("La demande doit etre creee par un etudiant.")

    @property
    def can_cancel_by_student(self):
        return self.statut == self.Statut.EN_ATTENTE_ENCADRANT

    def __str__(self):
        return f"DemandeWorkflow #{self.pk} - {self.etudiant} - {self.composant.nom}"


class Achat(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        RECU = "recu", "Recu"

    demande = models.ForeignKey(
        DemandeWorkflow,
        on_delete=models.CASCADE,
        related_name="achats",
    )
    composant = models.ForeignKey(
        Composant,
        on_delete=models.PROTECT,
        related_name="achats",
    )
    quantite_achetee = models.PositiveIntegerField()
    fournisseur = models.CharField(max_length=180)
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_COURS,
    )
    date_commande = models.DateTimeField(default=timezone.now)
    date_reception = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-date_commande"]
        db_table = "achats"

    def __str__(self):
        return f"Achat #{self.pk} - {self.composant.reference}"


class HistoriqueAction(models.Model):
    demande = models.ForeignKey(
        DemandeWorkflow,
        on_delete=models.CASCADE,
        related_name="historique_actions",
    )
    action = models.CharField(max_length=255)
    acteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="historique_actions",
    )
    date_action = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date_action"]
        db_table = "historique"

    def __str__(self):
        return f"{self.action} ({self.date_action:%Y-%m-%d %H:%M})"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        db_table = "notifications"

    def __str__(self):
        return f"Notification #{self.pk} - {self.user}"
