# LabResa

Plateforme web Django de gestion et reservation de materiel de laboratoire avec workflow multi-roles:

- ETUDIANT
- ENSEIGNANT
- LABRESPO
- SERVICE_3PH

Interface moderne type portail universitaire:
- sidebar verticale rouge fixe
- contenu principal clair
- cartes statistiques et tableaux Bootstrap 5
- design responsive

## Fonctionnalites principales

- Authentification Django (login/logout)
- Redirection automatique vers dashboard selon role
- Gestion des acces par role
- Gestion du stock materiel (CRUD complet)
- Demandes de materiel existant
- Demandes de nouveau materiel
- Commentaires/recommandations enseignant
- Validation/refus par LabRespo
- Confirmation de sortie/retour materiel
- Historisation des mouvements de stock
- Affectation groupe -> enseignant par service 3PH
- Administration Django configuree

## Arborescence

```text
LabResa/
├── LabResa/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── lab/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── mixins.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── seed_data.py
│   └── migrations/
│       └── __init__.py
├── media/
│   └── materials/
├── static/
│   └── css/
│       └── style.css
├── templates/
│   ├── base.html
│   ├── includes/
│   │   └── sidebar_nav.html
│   ├── registration/
│   │   └── login.html
│   ├── dashboard/
│   │   ├── etudiant_dashboard.html
│   │   ├── enseignant_dashboard.html
│   │   ├── labrespo_dashboard.html
│   │   └── service3ph_dashboard.html
│   ├── materials/
│   │   ├── materiel_confirm_delete.html
│   │   ├── materiel_detail.html
│   │   ├── materiel_form.html
│   │   ├── materiel_list.html
│   │   └── mouvement_list.html
│   ├── demands/
│   │   ├── demande_detail.html
│   │   ├── demande_existant_form.html
│   │   ├── demande_list.html
│   │   ├── demande_nouveau_form.html
│   │   ├── labrespo_decision_form.html
│   │   └── teacher_comment_form.html
│   └── groups/
│       ├── affectation_form.html
│       ├── group_detail.html
│       ├── service_group_list.html
│       ├── service_teacher_list.html
│       └── teacher_group_list.html
├── manage.py
└── requirements.txt
```

## Modele de donnees et relations

- `User` (custom auth user):
  - role: ETUDIANT / ENSEIGNANT / LABRESPO / SERVICE_3PH
  - departement, date_inscription, is_active
- `Groupe`
- `MembreGroupe`:
  - liaison ETUDIANT <-> GROUPE
- `AffectationGroupe`:
  - GROUPE -> ENSEIGNANT
  - attribue_par (SERVICE_3PH)
- `Materiel`
- `Demande`:
  - creee par ETUDIANT, rattachee a un GROUPE
  - type: EXISTANT / NOUVEAU
  - statut workflow
- `LigneDemande`:
  - lignes de materiel pour demande EXISTANT
- `DemandeNouveauMateriel`:
  - detail pour demande NOUVEAU
- `MouvementStock`:
  - historique sorties/retours valides par LABRESPO

## Installation et lancement

1. Se placer dans le dossier projet:

```bash
cd LabResa
```

2. Creer et activer un environnement virtuel:

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Installer les dependances:

```bash
pip install -r requirements.txt
```

4. Creer les migrations puis migrer:

```bash
python manage.py makemigrations
python manage.py migrate
```

5. Creer un superuser:

```bash
python manage.py createsuperuser
```

6. Charger les donnees de demonstration:

```bash
python manage.py seed_data
```

7. Lancer le serveur:

```bash
python manage.py runserver
```

## Comptes de test (mot de passe commun)

Mot de passe pour tous les comptes seed: `LabResa123!`

- LABRESPO: `labrespo`
- SERVICE_3PH: `service3ph`
- ENSEIGNANT: `enseignant1`, `enseignant2`
- ETUDIANT: `etudiant1`, `etudiant2`, `etudiant3`

## URLs utiles

- Login: `/login/`
- Admin: `/admin/`
- Dashboard automatique selon role: `/`

## Notes techniques

- Base de donnees: SQLite (dev)
- Upload images materiel via `MEDIA_ROOT/media/`
- Static files personnalises dans `static/css/style.css`
- Controle d'acces par role via `RoleRequiredMixin` + verifications explicites dans les vues FBV
