-- Script de création de la base de données des contraventions alimentaires
-- Ville de Montréal — INF5190 Projet de session

CREATE TABLE IF NOT EXISTS contravention (
    id_poursuite   INTEGER PRIMARY KEY,
    business_id    INTEGER,
    date           TEXT,
    description    TEXT,
    adresse        TEXT,
    date_jugement  TEXT,
    etablissement  TEXT,
    montant        INTEGER,
    proprietaire   TEXT,
    ville          TEXT,
    statut         TEXT,
    date_statut    TEXT,
    categorie      TEXT
);

CREATE TABLE IF NOT EXISTS demande_inspection (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    etablissement  TEXT    NOT NULL,
    adresse        TEXT    NOT NULL,
    ville          TEXT    NOT NULL,
    date_visite    TEXT    NOT NULL,
    prenom_client  TEXT    NOT NULL,
    nom_client     TEXT    NOT NULL,
    description    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS utilisateur (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_complet       TEXT    NOT NULL,
    courriel          TEXT    NOT NULL UNIQUE,
    mot_de_passe_hash TEXT    NOT NULL,
    photo_profil      BLOB,
    photo_mime        TEXT
);

CREATE TABLE IF NOT EXISTS utilisateur_etablissement (
    utilisateur_id  INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    etablissement   TEXT    NOT NULL,
    PRIMARY KEY (utilisateur_id, etablissement)
);
