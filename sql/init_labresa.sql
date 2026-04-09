-- PostgreSQL initialization script for LabResa prototype schema.
-- This SQL is provided for standalone DB bootstrap and testing.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('etudiant', 'encadrant', 'labo', 'achat', 'admin')),
    nom VARCHAR(120) NOT NULL,
    prenom VARCHAR(120) NOT NULL,
    classe VARCHAR(60),
    encadrant_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    departement VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS composants (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(180) NOT NULL,
    reference VARCHAR(80) UNIQUE NOT NULL,
    quantite_disponible INTEGER NOT NULL DEFAULT 0 CHECK (quantite_disponible >= 0),
    seuil_alerte INTEGER NOT NULL DEFAULT 0 CHECK (seuil_alerte >= 0),
    localisation VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS demandes (
    id SERIAL PRIMARY KEY,
    etudiant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    composant_id INTEGER NOT NULL REFERENCES composants(id) ON DELETE RESTRICT,
    quantite INTEGER NOT NULL CHECK (quantite > 0),
    statut VARCHAR(40) NOT NULL CHECK (
        statut IN (
            'en_attente_encadrant',
            'en_attente_labo',
            'en_attente_achat',
            'approuvee',
            'refusee',
            'terminee'
        )
    ),
    date_demande TIMESTAMP NOT NULL DEFAULT NOW(),
    commentaire_encadrant TEXT
);

CREATE TABLE IF NOT EXISTS achats (
    id SERIAL PRIMARY KEY,
    composant_id INTEGER NOT NULL REFERENCES composants(id) ON DELETE RESTRICT,
    quantite_achetee INTEGER NOT NULL CHECK (quantite_achetee > 0),
    fournisseur VARCHAR(180) NOT NULL,
    statut VARCHAR(20) NOT NULL CHECK (statut IN ('en_cours', 'recu')),
    date_commande TIMESTAMP NOT NULL DEFAULT NOW(),
    date_reception TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historique (
    id SERIAL PRIMARY KEY,
    demande_id INTEGER NOT NULL REFERENCES demandes(id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    acteur_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    date_action TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Demo rows (password hash placeholders).
INSERT INTO users (email, password_hash, role, nom, prenom, classe, departement)
VALUES
    ('admin3ph@labresa.local', 'HASH_PLACEHOLDER', 'admin', 'Admin', '3PH', NULL, NULL),
    ('encadrant1@labresa.local', 'HASH_PLACEHOLDER', 'encadrant', 'Encadrant', 'Un', NULL, 'Electronique'),
    ('labo1@labresa.local', 'HASH_PLACEHOLDER', 'labo', 'Labo', 'Temps', NULL, NULL),
    ('achat1@labresa.local', 'HASH_PLACEHOLDER', 'achat', 'Service', 'Achat', NULL, NULL),
    ('etudiant1@labresa.local', 'HASH_PLACEHOLDER', 'etudiant', 'Etudiant', 'Un', 'GI-3A', NULL)
ON CONFLICT (email) DO NOTHING;
