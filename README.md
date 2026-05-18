# Infractions Alimentaires Montréal

Application web permettant de consulter et rechercher les infractions alimentaires
sur le territoire de Montréal, avec un système de profils utilisateurs, de
notifications par courriel personnalisées et une API REST complète.

> Projet de session — INF5190 Hiver 2026, UQÀM

---

## Table des matières

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Stack technique](#stack-technique)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Lancement de l'application](#lancement-de-lapplication)
- [Interface web](#interface-web)
- [API REST](#api-rest)
- [Base de données](#base-de-données)
- [Structure du projet](#structure-du-projet)
- [Exemples d'utilisation de l'API](#exemples-dutilisation-de-lapi)

---

## Aperçu

Cette application agrège les données ouvertes de la Ville de Montréal sur les
contraventions alimentaires et les rend accessibles via :

- Une **interface web** interactive avec plusieurs modes de recherche
- Un **système de profils utilisateurs** avec authentification par session
- Des **alertes par courriel personnalisées** par établissement surveillé
- Un **lien de désabonnement** sécurisé (token HMAC signé) dans chaque alerte
- Une **API REST** documentée (JSON, XML, CSV)
- Un **formulaire de plainte** permettant aux citoyens de soumettre une demande d'inspection

Les données sont synchronisées automatiquement chaque nuit depuis le portail
des données ouvertes de Montréal.

---

## Fonctionnalités

### Gestion des données
- Téléchargement automatique du fichier CSV depuis le portail de données ouvertes de Montréal
- Import dans la base de données SQLite avec déduplication (`INSERT OR IGNORE`)
- Synchronisation quotidienne à minuit via un planificateur en arrière-plan (APScheduler)

### Interface web
| Fonctionnalité | Description |
|---|---|
| Recherche par formulaire | Recherche par nom d'établissement, propriétaire ou rue |
| Recherche par plage de dates | Établissements ayant reçu des infractions entre deux dates (Ajax) |
| Recherche par établissement | Toutes les infractions d'un établissement sélectionné (Ajax) |
| Formulaire de plainte | Soumission de demandes d'inspection par les citoyens |
| Inscription / Connexion | Création de profil et authentification par session Flask |
| Page de profil | Gestion de la liste d'établissements surveillés et photo de profil |
| Désabonnement | Page de confirmation via lien sécurisé reçu par courriel |
| Documentation API | Page de documentation RAML interactive |

### Notifications par courriel
- **B1** — Détection des nouveaux contrevenants et envoi d'un rapport à l'adresse configurée
- **E3** — Courriel personnalisé à chaque utilisateur abonné à un établissement contrevenant
- **E4** — Lien de désabonnement signé (HMAC-SHA256) inclus dans chaque alerte

### API REST
| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/contrevenants` | Infractions entre deux dates (`du` et `au`) |
| GET | `/api/etablissements` | Tous les établissements avec leur nombre d'infractions (JSON) |
| GET | `/api/etablissements.xml` | Même données en format XML |
| GET | `/api/etablissements.csv` | Même données en format CSV (téléchargeable) |
| GET | `/api/etablissement/<nom>` | Toutes les infractions d'un établissement |
| POST | `/api/inspections` | Créer une demande d'inspection |
| DELETE | `/api/inspections/<id>` | Supprimer une demande d'inspection |
| POST | `/api/utilisateurs` | Créer un profil utilisateur (json-schema) |
| POST | `/api/connexion` | Authentifier un utilisateur (ouvre une session) |
| POST | `/api/deconnexion` | Fermer la session courante |
| PUT | `/api/utilisateurs/<id>/etablissements` | Mettre à jour les établissements surveillés |
| POST | `/api/utilisateurs/<id>/photo` | Téléverser une photo de profil (jpg/png) |
| GET | `/api/utilisateurs/<id>/photo` | Obtenir la photo de profil |
| DELETE | `/api/desabonnement` | Se désabonner via token signé |

---

## Stack technique

**Backend**
- Python 3.13
- Flask 3.1.0 (+ Werkzeug pour le hachage de mots de passe)
- SQLite3
- APScheduler 3.10.4
- jsonschema 4.23.0
- PyYAML 6.0.2
- requests 2.32.3

**Frontend**
- HTML5 + Jinja2
- Bootstrap 5.3.3
- JavaScript Vanilla (Fetch API, async/await)
- CSS3 (Flexbox, animations)

**Sécurité**
- Mots de passe hachés avec `werkzeug.security` (PBKDF2)
- Tokens de désabonnement signés HMAC-SHA256
- Requêtes SQL paramétrées (protection contre l'injection SQL)
- Sessions Flask côté serveur

---

## Prérequis

- Python 3.10 ou supérieur
- pip

---

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/<votre-username>/infractions-alimentaires-mtl.git
cd infractions-alimentaires-mtl

# 2. Créer un environnement virtuel
python -m venv venv

# Activer l'environnement (Windows)
venv\Scripts\activate

# Activer l'environnement (Linux/macOS)
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Initialiser la base de données
python -c "import sqlite3; conn = sqlite3.connect('db/db.sqlite'); conn.executescript(open('db/db.sql').read()); conn.close()"

# 5. Télécharger et importer les données initiales
python get_data.py
```

---

## Configuration

Remplissez `config.yaml` avec vos informations SMTP et une clé secrète :

```yaml
courriel:
  expediteur: votre-adresse@gmail.com
  destinataire: destinataire@exemple.com
  serveur_smtp: smtp.gmail.com
  port_smtp: 587
  mot_de_passe: votre-mot-de-passe-application

secret_key: une-chaine-secrete-longue-et-aleatoire
```

> Pour Gmail, utilisez un [mot de passe d'application](https://myaccount.google.com/apppasswords)
> et non votre mot de passe principal.

La `secret_key` est utilisée pour signer les tokens de désabonnement (E4) et
chiffrer les sessions Flask.

---

## Lancement de l'application

```bash
python app.py
```

L'application sera disponible à l'adresse : [http://localhost:5000](http://localhost:5000)

Le planificateur de synchronisation démarre automatiquement avec l'application.

---

## Interface web

### Page d'accueil — `/`

Trois onglets de recherche :

1. **Recherche générale** — Par nom d'établissement, propriétaire ou rue
2. **Par période** — Établissements contrevenants entre deux dates (Ajax)
3. **Par établissement** — Toutes les infractions d'un restaurant sélectionné (Ajax)

### Page de résultats — `/resultats`

Affiche les contraventions sous forme de cartes avec badge de statut (Ouvert / Fermé).

### Formulaire de plainte — `/plainte`

Permet à un citoyen de soumettre une demande d'inspection. Champs requis :
nom, prénom, établissement, adresse, ville, date de visite, description.

### Inscription — `/inscription`

Création d'un profil utilisateur. Champs requis :
- Nom complet
- Adresse courriel
- Mot de passe (6 caractères minimum)
- Liste d'établissements à surveiller (optionnel, modifiable après)

### Connexion — `/connexion`

Authentification par courriel et mot de passe. Ouvre une session Flask.

### Profil — `/profil` *(session requise)*

Accessible uniquement après connexion. Permet de :
- **Modifier la liste** d'établissements surveillés (ajout/retrait + sauvegarde)
- **Téléverser une photo de profil** (formats jpg et png acceptés)
- **Se déconnecter**

### Désabonnement — `/desabonnement?token=<token>`

Page de confirmation pour se désabonner des alertes d'un établissement.
Accessible via le lien inclus dans les courriels d'alerte (E3/E4).

### Documentation API — `/doc`

Page de documentation RAML listant tous les endpoints avec leurs paramètres
et exemples de réponses.

---

## API REST

### `GET /contrevenants`

Retourne les infractions enregistrées entre deux dates.

| Paramètre | Type | Description |
|---|---|---|
| `du` | string | Date de début (YYYY-MM-DD) |
| `au` | string | Date de fin (YYYY-MM-DD) |

**Exemple de réponse :**
```json
[
  {
    "etablissement": "Restaurant XYZ",
    "nb_contraventions": 3
  }
]
```

---

### `POST /api/utilisateurs`

Crée un profil utilisateur. Corps JSON requis :

```json
{
  "nom_complet": "Marie Tremblay",
  "courriel": "marie@exemple.com",
  "mot_de_passe": "secret123",
  "etablissements_surveilles": ["Restaurant Pho", "Brasserie du Nord"]
}
```

| Code | Description |
|---|---|
| `201` | Profil créé, retourne `{"id": 1}` |
| `400` | Données invalides (json-schema) |
| `409` | Adresse courriel déjà utilisée |

---

### `POST /api/connexion`

Authentifie un utilisateur et ouvre une session Flask.

```json
{ "courriel": "marie@exemple.com", "mot_de_passe": "secret123" }
```

---

### `PUT /api/utilisateurs/<id>/etablissements`

Remplace la liste des établissements surveillés (session requise).

```json
{ "etablissements": ["Restaurant A", "Café B"] }
```

---

### `POST /api/utilisateurs/<id>/photo`

Téléverse une photo de profil. Envoyer en `multipart/form-data`, champ `photo`.
Formats acceptés : `image/jpeg`, `image/png`.

---

### `DELETE /api/desabonnement`

Se désabonne d'un établissement via un token signé reçu par courriel.

```json
{ "token": "<token_signe>" }
```

---

### `POST /api/inspections`

Crée une demande d'inspection. Corps JSON requis :

```json
{
  "etablissement": "Restaurant ABC",
  "adresse": "456 Avenue du Parc",
  "ville": "Montréal",
  "date_visite": "2024-04-01",
  "prenom_client": "Marie",
  "nom_client": "Tremblay",
  "description": "Présence de nuisibles constatée lors de ma visite."
}
```

---

### `DELETE /api/inspections/<id>`

Supprime une demande d'inspection par son identifiant.

---

## Base de données

### Table `contravention`

| Colonne | Type | Description |
|---|---|---|
| `id_poursuite` | INTEGER (PK) | Identifiant unique de la poursuite |
| `business_id` | INTEGER | Identifiant de l'établissement |
| `date` | TEXT | Date de l'infraction |
| `description` | TEXT | Description de l'infraction |
| `adresse` | TEXT | Adresse de l'établissement |
| `date_jugement` | TEXT | Date du jugement |
| `etablissement` | TEXT | Nom de l'établissement |
| `montant` | INTEGER | Montant de l'amende |
| `proprietaire` | TEXT | Nom du propriétaire |
| `ville` | TEXT | Ville |
| `statut` | TEXT | Statut (Ouvert / Fermé) |
| `date_statut` | TEXT | Date du changement de statut |
| `categorie` | TEXT | Catégorie d'infraction |

### Table `demande_inspection`

| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Identifiant auto-incrémenté |
| `etablissement` | TEXT | Nom de l'établissement |
| `adresse` | TEXT | Adresse |
| `ville` | TEXT | Ville |
| `date_visite` | TEXT | Date de la visite du client |
| `prenom_client` | TEXT | Prénom du client |
| `nom_client` | TEXT | Nom du client |
| `description` | TEXT | Description de la plainte |

### Table `utilisateur`

| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Identifiant auto-incrémenté |
| `nom_complet` | TEXT | Nom complet de l'utilisateur |
| `courriel` | TEXT (UNIQUE) | Adresse courriel |
| `mot_de_passe_hash` | TEXT | Mot de passe haché (PBKDF2) |
| `photo_profil` | BLOB | Photo de profil (jpg/png) |
| `photo_mime` | TEXT | Type MIME de la photo |

### Table `utilisateur_etablissement`

| Colonne | Type | Description |
|---|---|---|
| `utilisateur_id` | INTEGER (FK) | Référence vers `utilisateur.id` |
| `etablissement` | TEXT | Nom de l'établissement surveillé |

---

## Structure du projet

```
Projet de Session/
├── app.py                  # Application Flask — routes et logique principale
├── database.py             # Couche d'accès aux données (DAL)
├── get_data.py             # Téléchargement et import des données CSV
├── scheduler.py            # Planificateur de tâches en arrière-plan
├── mail_service.py         # Notifications courriel (B1, E3, E4)
├── config.yaml             # Configuration SMTP et clé secrète
├── requirements.txt        # Dépendances Python
├── doc.raml                # Spécification RAML de l'API
│
├── db/
│   ├── db.sql              # Schéma de la base de données (4 tables)
│   └── db.sqlite           # Fichier de base de données SQLite
│
├── templates/
│   ├── base.html           # Template de base (navbar, footer)
│   ├── index.html          # Page d'accueil avec les 3 formulaires de recherche
│   ├── resultats.html      # Page de résultats de recherche
│   ├── plainte.html        # Formulaire de demande d'inspection
│   ├── inscription.html    # Formulaire d'inscription utilisateur
│   ├── connexion.html      # Formulaire de connexion
│   ├── profil.html         # Page de profil (établissements + photo)
│   ├── desabonnement.html  # Confirmation de désabonnement
│   ├── doc.html            # Documentation API
│   └── erreur.html         # Pages d'erreur (404/500)
│
└── static/
    ├── css/
    │   └── style.css           # Styles personnalisés
    └── js/
        ├── recherche.js        # Ajax — recherche par dates (A5)
        ├── restaurant.js       # Ajax — recherche par établissement (A6)
        ├── plainte.js          # Ajax — formulaire de plainte (D1)
        ├── inscription.js      # Ajax — création de profil (E1/E2)
        ├── connexion.js        # Ajax — authentification (E2)
        ├── profil.js           # Ajax — gestion profil et photo (E2)
        └── desabonnement.js    # Ajax — confirmation désabonnement (E4)
```

---

## Exemples d'utilisation de l'API

```bash
# Infractions entre deux dates
curl "http://localhost:5000/contrevenants?du=2024-01-01&au=2024-03-31"

# Tous les établissements en JSON
curl "http://localhost:5000/api/etablissements"

# Tous les établissements en XML
curl "http://localhost:5000/api/etablissements.xml"

# Télécharger le CSV
curl -O "http://localhost:5000/api/etablissements.csv"

# Infractions d'un établissement spécifique
curl "http://localhost:5000/api/etablissement/Restaurant%20XYZ"

# Créer une demande d'inspection
curl -X POST "http://localhost:5000/api/inspections" \
  -H "Content-Type: application/json" \
  -d '{
    "etablissement": "Restaurant ABC",
    "adresse": "456 Ave du Parc",
    "ville": "Montreal",
    "date_visite": "2024-04-01",
    "prenom_client": "Marie",
    "nom_client": "Tremblay",
    "description": "Présence de nuisibles."
  }'

# Supprimer une demande d'inspection
curl -X DELETE "http://localhost:5000/api/inspections/1"

# Créer un profil utilisateur
curl -X POST "http://localhost:5000/api/utilisateurs" \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "Marie Tremblay",
    "courriel": "marie@exemple.com",
    "mot_de_passe": "secret123",
    "etablissements_surveilles": ["Restaurant Pho"]
  }'

# Se connecter (avec sauvegarde du cookie de session)
curl -X POST "http://localhost:5000/api/connexion" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"courriel": "marie@exemple.com", "mot_de_passe": "secret123"}'

# Mettre à jour les établissements surveillés
curl -X PUT "http://localhost:5000/api/utilisateurs/1/etablissements" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"etablissements": ["Restaurant Pho", "Cafe du Coin"]}'
```

---

## Licence

Projet académique — UQÀM INF5190, Hiver 2026.

Les données utilisées proviennent du portail des
[données ouvertes de la Ville de Montréal](https://donnees.montreal.ca)
et sont soumises à leur propre licence.
