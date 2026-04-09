from django.contrib.auth import get_user_model
from rest_framework import serializers

from lab.models import Achat, Composant, DemandeWorkflow, Notification

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserMeSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role_api")

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
            "encadrant",
            "is_active",
        ]

    def validate_encadrant(self, value):
        if value and value.role not in [User.Role.ENCADRANT, User.Role.ENSEIGNANT]:
            raise serializers.ValidationError("Encadrant invalide.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None) or "ChangeMe123!"
        user = User(**validated_data)
        user.role = User.Role.ETUDIANT
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.role = User.Role.ETUDIANT
        if password:
            instance.set_password(password)
        instance.save()
        return instance
