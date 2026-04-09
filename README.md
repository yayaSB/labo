# LabResa

Application web complete de gestion et reservation de materiel de laboratoire universitaire.

Cette version contient:
- Backend Django (API REST JWT + RBAC + ORM securise)
- Frontend React (Vite + React Router + Axios + Bootstrap + Chart.js)
- Base SQLite pour prototype (compatible extension PostgreSQL)
- Workflow metier complet (etudiant -> encadrant -> labo -> achat -> labo)

## Architecture

```text
.
├── LabResa/                  # Config Django
├── lab/                      # App metier + models + admin + seeds
├── api/                      # API REST (auth, roles, endpoints)
├── frontend/                 # React app (dashboards par role)
├── sql/init_labresa.sql      # Script SQL init PostgreSQL
├── manage.py
├── requirements.txt
└── package.json              # npm scripts fullstack
```

## Stack

- Backend: Django 5 + Django REST Framework
- Auth: JWT (SimpleJWT) + blacklist refresh tokens
- Roles: RBAC par middleware/permissions API
- DB: SQLite (prototype)
- Frontend: React + Vite + Bootstrap + Chart.js
- CORS: django-cors-headers

## Roles API supportes

- `etudiant`
- `encadrant`
- `labo`
- `achat`
- `admin` (Service 3PH)

Le mapping est gere via `User.role_api`:
- `ETUDIANT -> etudiant`
- `ENCADRANT` ou `ENSEIGNANT -> encadrant`
- `LABO_TEMPS` ou `LABRESPO -> labo`
- `SERVICE_ACHAT -> achat`
- `SERVICE_3PH -> admin`

## Setup local

### 1) Python env

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Migration DB

```bash
python manage.py migrate
```

### 3) Seed donnees demo

```bash
python manage.py seed_platform_data
```

### 4) Installer frontend + scripts fullstack

```bash
npm install
```

### 5) Lancer backend + frontend ensemble

```bash
npm run dev
```

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

## Variables d'environnement (optionnel)

Frontend:
- `VITE_API_BASE_URL` (defaut: `http://127.0.0.1:8000/api`)

Backend (pour prod, a configurer selon environnement):
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DATABASE_URL` (si PostgreSQL)
- SMTP settings (si emails reels)

## Comptes de test

Commande seed: `python manage.py seed_platform_data`

Mot de passe commun: `LabResa123!`

- Admin 3PH: `admin3ph`
- Encadrant: `encadrant1`
- Labo: `labo1`
- Achat: `achat1`
- Etudiants: `etudiant1`, `etudiant2`

## Endpoints API implementes

Auth:
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`

Etudiant:
- `GET /api/composants`
- `POST /api/demandes`
- `GET /api/mes-demandes`
- `DELETE /api/demande/:id`

Encadrant:
- `GET /api/demandes/classe`
- `PUT /api/demande/:id/valider-encadrant`
- `PUT /api/demande/:id/refuser-encadrant`

Labo:
- `GET /api/demandes/attente-labo`
- `PUT /api/demande/:id/reserver`
- `GET /api/composants`
- `POST /api/composants`
- `PUT /api/composants/:id`

Service Achat:
- `GET /api/demandes/attente-achat`
- `GET /api/achats`
- `POST /api/achats`
- `PUT /api/achats/:id/receptionner`

Admin (3PH):
- `GET /api/encadrants`
- `POST /api/encadrants`
- `GET /api/encadrants/:id`
- `PUT /api/encadrants/:id`
- `DELETE /api/encadrants/:id`
- `GET /api/etudiants`
- `POST /api/etudiants`
- `PUT /api/etudiants/:id`
- `DELETE /api/etudiants/:id`
- `GET /api/statistiques`
- `GET /api/rapports?format=csv|pdf`

Notifications:
- `GET /api/notifications`
- `PUT /api/notifications/:id/read`

## Workflow metier implemente

1. Etudiant cree demande -> `en_attente_encadrant`
2. Encadrant valide -> `en_attente_labo`, ou refuse -> `refusee`
3. Labo reserve:
   - stock OK -> `approuvee` + decrement stock
   - stock KO -> `en_attente_achat` + notification achat
4. Achat cree commande -> statut achat `en_cours`
5. Achat receptionne:
   - achat -> `recu`
   - stock composant augmente
   - demande -> `en_attente_labo`
6. Labo peut finaliser ensuite vers `approuvee`
7. Cloture manuelle possible vers `terminee` selon votre logique operationnelle

## Securite et qualite

- Passwords hash via `set_password`
- ORM Django (pas de SQL brut) pour eviter injections
- JWT + refresh blacklist
- Permissions RBAC strictes par endpoint
- Validation entree via serializers DRF
- Transactions atomiques sur operations stock/achat
- Historique d'actions + notifications in-app + email console

## SQL PostgreSQL

Le fichier `sql/init_labresa.sql` fournit:
- creation tables attendues (`users`, `composants`, `demandes`, `achats`, `historique`, `notifications`)
- jeux de donnees de base

Vous pouvez l'utiliser pour un bootstrap hors ORM Django si necessaire.
