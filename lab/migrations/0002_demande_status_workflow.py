from django.db import migrations, models


def migrate_old_statuses_forward(apps, schema_editor):
    Demande = apps.get_model("lab", "Demande")
    status_mapping = {
        "EN_ATTENTE": "EN_ATTENTE_VALIDATION_ENSEIGNANT",
        "COMMENTEE": "VALIDEE_PAR_ENSEIGNANT",
        "VALIDEE": "EN_COURS_TRAITEMENT",
        "EN_COURS": "RETIREE",
        "RETOURNEE": "TERMINEE",
    }
    for old_status, new_status in status_mapping.items():
        Demande.objects.filter(statut=old_status).update(statut=new_status)


def migrate_old_statuses_backward(apps, schema_editor):
    Demande = apps.get_model("lab", "Demande")
    status_mapping = {
        "EN_ATTENTE_VALIDATION_ENSEIGNANT": "EN_ATTENTE",
        "VALIDEE_PAR_ENSEIGNANT": "COMMENTEE",
        "EN_COURS_TRAITEMENT": "VALIDEE",
        "EN_PAUSE": "VALIDEE",
        "DISPONIBLE": "VALIDEE",
        "RETIREE": "EN_COURS",
        "TERMINEE": "RETOURNEE",
    }
    for new_status, old_status in status_mapping.items():
        Demande.objects.filter(statut=new_status).update(statut=old_status)


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="demande",
            name="statut",
            field=models.CharField(
                choices=[
                    (
                        "EN_ATTENTE_VALIDATION_ENSEIGNANT",
                        "En attente de validation enseignant",
                    ),
                    ("VALIDEE_PAR_ENSEIGNANT", "Validee par enseignant"),
                    ("EN_COURS_TRAITEMENT", "En cours de traitement"),
                    ("EN_PAUSE", "En pause"),
                    ("DISPONIBLE", "Disponible"),
                    ("REFUSEE", "Refusee"),
                    ("RETIREE", "Retiree"),
                    ("TERMINEE", "Terminee"),
                ],
                default="EN_ATTENTE_VALIDATION_ENSEIGNANT",
                max_length=40,
            ),
        ),
        migrations.RunPython(
            migrate_old_statuses_forward,
            migrate_old_statuses_backward,
        ),
    ]
