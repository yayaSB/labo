from django.contrib.auth import get_user_model
from rest_framework import serializers

from lab.models import Achat, Composant, DemandeWorkflow, Groupe, MembreGroupe, Notification

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserMeSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role_api")
    encadrants = serializers.SerializerMethodField()
    groupes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "classe",
            "departement",
            "encadrants",
            "groupes",
        ]

    def get_encadrants(self, obj):
        if obj.role != User.Role.ETUDIANT:
            return []
        return [
            {
                "id": e.id,
                "username": e.username,
                "nom": e.get_full_name() or e.username,
            }
            for e in obj.get_encadrants()
        ]

    def get_groupes(self, obj):
        if obj.role != User.Role.ETUDIANT:
            return []
        return [
            {"id": g.id, "nom_groupe": g.nom_groupe}
            for g in Groupe.objects.filter(membres__etudiant=obj).distinct()
        ]


class ComposantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Composant
        fields = [
            "id",
            "nom",
            "reference",
            "quantite_disponible",
            "seuil_alerte",
            "localisation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class DemandeCreateSerializer(serializers.Serializer):
    composant_id = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)

    def validate_composant_id(self, value):
        if not Composant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Composant introuvable.")
        return value


class DemandeWorkflowSerializer(serializers.ModelSerializer):
    etudiant_nom = serializers.SerializerMethodField()
    composant_nom = serializers.CharField(source="composant.nom", read_only=True)
    composant_reference = serializers.CharField(source="composant.reference", read_only=True)

    class Meta:
        model = DemandeWorkflow
        fields = [
            "id",
            "etudiant",
            "etudiant_nom",
            "composant",
            "composant_nom",
            "composant_reference",
            "quantite",
            "statut",
            "date_demande",
            "date_derniere_maj",
            "commentaire_encadrant",
        ]
        read_only_fields = [
            "id",
            "etudiant",
            "date_demande",
            "date_derniere_maj",
            "commentaire_encadrant",
        ]

    def get_etudiant_nom(self, obj):
        return obj.etudiant.get_full_name() or obj.etudiant.username


class EncadrantDecisionSerializer(serializers.Serializer):
    commentaire_encadrant = serializers.CharField(required=False, allow_blank=True)


class AchatCreateSerializer(serializers.Serializer):
    demande_id = serializers.IntegerField()
    fournisseur = serializers.CharField(max_length=180)
    quantite_achetee = serializers.IntegerField(min_value=1)

    def validate_demande_id(self, value):
        if not DemandeWorkflow.objects.filter(id=value).exists():
            raise serializers.ValidationError("Demande introuvable.")
        return value


class AchatSerializer(serializers.ModelSerializer):
    composant_reference = serializers.CharField(source="composant.reference", read_only=True)

    class Meta:
        model = Achat
        fields = [
            "id",
            "demande",
            "composant",
            "composant_reference",
            "quantite_achetee",
            "fournisseur",
            "statut",
            "date_commande",
            "date_reception",
        ]
        read_only_fields = ["statut", "date_commande", "date_reception"]


class EncadrantAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "departement",
            "is_active",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None) or "ChangeMe123!"
        user = User(**validated_data)
        user.role = User.Role.ENCADRANT
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.role = User.Role.ENCADRANT
        instance.save()
        return instance


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]


class StudentAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    groupes = serializers.SerializerMethodField(read_only=True)
    groupes_etudiant = serializers.PrimaryKeyRelatedField(
        queryset=Groupe.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    encadrant = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.ENCADRANT),
        required=False,
        allow_null=True,
        write_only=True,
    )
    encadrants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.ENCADRANT),
        many=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "classe",
            "groupes",
            "groupes_etudiant",
            "encadrant",
            "encadrants",
            "is_active",
        ]

    def validate(self, attrs):
        groupes = attrs.get("groupes_etudiant")
        if self.instance is None and not groupes:
            raise serializers.ValidationError(
                {"groupes_etudiant": "Attribuez au moins un groupe a l'etudiant."}
            )
        if self.instance is not None and "groupes_etudiant" in attrs and not groupes:
            raise serializers.ValidationError(
                {"groupes_etudiant": "Un etudiant doit appartenir a au moins un groupe."}
            )
        return attrs

    def _sync_groupes(self, user, groupes):
        if groupes is None:
            return
        selected_ids = {g.id for g in groupes}
        existing_ids = set(
            MembreGroupe.objects.filter(etudiant=user).values_list("groupe_id", flat=True)
        )
        remove_ids = existing_ids - selected_ids
        add_ids = selected_ids - existing_ids
        if remove_ids:
            MembreGroupe.objects.filter(etudiant=user, groupe_id__in=remove_ids).delete()
        for groupe_id in add_ids:
            MembreGroupe.objects.create(etudiant=user, groupe_id=groupe_id)

    def get_groupes(self, instance):
        return [
            {"id": g.id, "nom_groupe": g.nom_groupe}
            for g in Groupe.objects.filter(membres__etudiant=instance).distinct()
        ]

    def create(self, validated_data):
        groupes = validated_data.pop("groupes_etudiant", [])
        single_encadrant = validated_data.pop("encadrant", None)
        encadrants = validated_data.pop("encadrants", [])
        if single_encadrant and not encadrants:
            encadrants = [single_encadrant]
        password = validated_data.pop("password", None) or "ChangeMe123!"
        user = User(**validated_data)
        user.role = User.Role.ETUDIANT
        user.set_password(password)
        user.save()
        self._sync_groupes(user, groupes)
        if encadrants:
            user.encadrants.set(encadrants)
            user.encadrant = encadrants[0]
            user.save(update_fields=["encadrant"])
        return user

    def update(self, instance, validated_data):
        groupes = validated_data.pop("groupes_etudiant", None)
        single_encadrant = validated_data.pop("encadrant", None)
        encadrants = validated_data.pop("encadrants", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.role = User.Role.ETUDIANT
        if password:
            instance.set_password(password)
        instance.save()
        self._sync_groupes(instance, groupes)
        if single_encadrant and encadrants is None:
            encadrants = [single_encadrant]
        if encadrants is not None:
            instance.encadrants.set(encadrants)
            first = encadrants[0] if encadrants else None
            instance.encadrant = first
            instance.save(update_fields=["encadrant"])
        return instance
