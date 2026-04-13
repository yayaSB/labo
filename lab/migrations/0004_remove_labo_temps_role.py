from django.db import migrations, models


def map_labo_temps_to_labrespo(apps, schema_editor):
    User = apps.get_model("lab", "User")
    User.objects.filter(role="LABO_TEMPS").update(role="LABRESPO")


def reverse_map_noop(apps, schema_editor):
    # No deterministic reverse mapping needed.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0003_composant_user_classe_user_encadrant_alter_user_role_and_more"),
    ]

    operations = [
        migrations.RunPython(map_labo_temps_to_labrespo, reverse_map_noop),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("ETUDIANT", "Etudiant"),
                    ("ENCADRANT", "Encadrant"),
                    ("ENSEIGNANT", "Enseignant"),
                    ("LABRESPO", "LabRespo"),
                    ("SERVICE_ACHAT", "Service Achat"),
                    ("SERVICE_3PH", "Service 3PH"),
                ],
                default="SERVICE_3PH",
                max_length=20,
            ),
        ),
    ]
