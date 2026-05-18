# INF5190 Projet de session Hiver 2026

## Instructions de démarrage

### Prérequis

```bash
pip install -r requirements.txt
```

### Initialiser la base de données et importer les données

```bash
# La base de données vide est déjà fournie dans db/db.sqlite
# Pour importer les données de la Ville de Montréal :
python get_data.py
```

### Démarrer l'application

```bash
python app.py
```

L'application est accessible à l'adresse : `http://localhost:5000`

---

## Fonctionnalités développées

### A1 — Téléchargement et importation des données (10 XP)

**Script :** `get_data.py`  
**Base de données :** `db/db.sqlite` (vide fournie), `db/db.sql` (script de création)

**Comment tester :**

```bash
python get_data.py
```

Le script télécharge le CSV de la Ville de Montréal et insère les nouvelles
contraventions dans la base de données (les doublons sont ignorés via `INSERT OR IGNORE`).

---

### A2 — Application Flask avec recherche (10 XP)

**Fichiers :** `app.py`, `database.py`, `templates/`

**Comment tester :**

1. Démarrer l'application : `python app.py`
2. Ouvrir `http://localhost:5000`
3. Choisir un critère de recherche (Nom d'établissement / Propriétaire / Rue)
4. Saisir une valeur (ex. : `pizza`, `rosemont`, `inc`) et soumettre
5. Les résultats s'affichent sur une nouvelle page avec toutes les données

**Exemples de recherche :**
- Établissement : `restaurant`
- Propriétaire : `9068`
- Rue : `rosemont`

---

### A3 — Synchronisation quotidienne automatique (5 XP)

**Fichier :** `scheduler.py`

Le `BackgroundScheduler` démarre automatiquement avec l'application Flask.
Il exécute la synchronisation des données chaque jour à minuit.

**Comment tester :**  
La tâche est enregistrée au démarrage de l'application. Pour tester manuellement,
appeler directement la fonction :

```python
from scheduler import synchroniser_donnees
synchroniser_donnees()
```

---

### A4 — Service REST par période de dates (10 XP)

**Route :** `GET /contrevenants?du=YYYY-MM-DD&au=YYYY-MM-DD`  
**Documentation RAML :** `GET /doc`

**Comment tester :**

```bash
curl "http://localhost:5000/contrevenants?du=2022-05-08&au=2024-05-15"
```

Ou ouvrir dans un navigateur :
`http://localhost:5000/contrevenants?du=2022-05-08&au=2024-05-15`

La réponse JSON contient la liste des établissements et leur nombre de contraventions
pour la période spécifiée.

**Documentation :** `http://localhost:5000/doc`

**Erreurs gérées :**
- `400` si les paramètres `du` ou `au` sont absents
- `400` si la date de début est postérieure à la date de fin

---

### A5 — Recherche Ajax par dates (10 XP)

**Fichier JS :** `static/js/recherche.js`

**Comment tester :**

1. Ouvrir `http://localhost:5000`
2. Dans la section « Contrevenants entre deux dates », saisir deux dates
3. Cliquer sur « Rechercher »
4. Un tableau s'affiche dynamiquement avec : établissement | nb contraventions

---

### A6 — Recherche Ajax par restaurant (10 XP)

**Fichier JS :** `static/js/restaurant.js`  
**Route REST :** `GET /api/etablissement/<nom>`

**Comment tester :**

1. Ouvrir `http://localhost:5000`
2. Dans la section « Infractions d'un restaurant », choisir un établissement
   dans la liste déroulante
3. Cliquer sur « Voir les infractions »
4. Les infractions s'affichent dynamiquement sous forme de cartes

---

### C1 — Service REST établissements en JSON (10 XP)

**Route :** `GET /api/etablissements`

**Comment tester :**

```bash
curl http://localhost:5000/api/etablissements
```

Retourne la liste de tous les établissements triés par nombre d'infractions
décroissant, en format JSON.

**Documentation :** `http://localhost:5000/doc`

---

### C2 — Service REST établissements en XML (5 XP)

**Route :** `GET /api/etablissements.xml`

**Comment tester :**

```bash
curl http://localhost:5000/api/etablissements.xml
```

Retourne les mêmes données en format XML UTF-8.

**Documentation :** `http://localhost:5000/doc`

---

### C3 — Service REST établissements en CSV (5 XP)

**Route :** `GET /api/etablissements.csv`

**Comment tester :**

```bash
curl http://localhost:5000/api/etablissements.csv
```

Retourne les mêmes données en format CSV UTF-8.

**Documentation :** `http://localhost:5000/doc`

---

### D1 — Service REST création d'inspection + page plainte (15 XP)

**Route :** `POST /api/inspections`  
**Page web :** `GET /plainte`  
**Validation :** json-schema (bibliothèque `jsonschema`)

**Comment tester via curl :**

```bash
curl -X POST http://localhost:5000/api/inspections \
  -H "Content-Type: application/json" \
  -d '{
    "etablissement": "Restaurant Test",
    "adresse": "123 Rue Principale",
    "ville": "Montréal",
    "date_visite": "2024-03-15",
    "prenom_client": "Jean",
    "nom_client": "Tremblay",
    "description": "Présence de rongeurs observée."
  }'
```

Réponse `201` avec l'identifiant de la demande créée.

**Comment tester via la page web :**

1. Ouvrir `http://localhost:5000/plainte`
2. Remplir le formulaire
3. Soumettre — un message de confirmation s'affiche

**Erreurs gérées :**
- `400` si le corps JSON est absent ou invalide
- `400` si un champ requis manque
- `400` si le format de `date_visite` n'est pas `YYYY-MM-DD`

**Documentation :** `http://localhost:5000/doc`

---

### D2 — Service REST suppression d'inspection (5 XP)

**Route :** `DELETE /api/inspections/<id>`

**Comment tester :**

```bash
# Créer d'abord une demande (voir D1), puis supprimer avec son id
curl -X DELETE http://localhost:5000/api/inspections/1
```

- `200` si la suppression réussit
- `404` si la demande n'existe pas

**Documentation :** `http://localhost:5000/doc`

---

### B1 — Détection nouvelles contraventions + envoi courriel (5 XP)

**Fichiers :** `mail_service.py`, `config.yaml`

**Configuration :** Modifier `config.yaml` avec les paramètres SMTP :

```yaml
courriel:
  expediteur: votre.courriel@gmail.com
  destinataire: destinataire@exemple.com
  serveur_smtp: smtp.gmail.com
  port_smtp: 587
  mot_de_passe: votre_mot_de_passe_application
```

**Fonctionnement :**  
À chaque synchronisation (minuit via le scheduler), le système compare les
identifiants de contraventions en base avec le CSV téléchargé. Si de nouveaux
établissements sont détectés, un courriel est envoyé automatiquement.

**Comment tester manuellement :**

```python
from mail_service import notifier_nouvelles_contraventions
# Simuler une nouvelle contravention avec un id inexistant
notifier_nouvelles_contraventions([
    {"id_poursuite": 999999, "etablissement": "RESTAURANT TEST"}
])
```

---

### E1 — Création de profil utilisateur via API REST (15 XP)

**Route :** `POST /api/utilisateurs`  
**Validation :** json-schema (`SCHEMA_UTILISATEUR` dans `app.py`)  
**Fichiers :** `app.py`, `database.py`, `db/db.sql`

**Corps JSON requis :**

```json
{
  "nom_complet": "Marie Tremblay",
  "courriel": "marie@exemple.com",
  "mot_de_passe": "motdepasse123",
  "etablissements_surveilles": ["Restaurant Pho", "Brasserie du Nord"]
}
```

**Comment tester :**

```bash
curl -X POST http://localhost:5000/api/utilisateurs \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "Marie Tremblay",
    "courriel": "marie@exemple.com",
    "mot_de_passe": "motdepasse123",
    "etablissements_surveilles": []
  }'
```

- `201` avec l'`id` du nouvel utilisateur si succès
- `400` si le JSON est invalide ou un champ manque
- `409` si l'adresse courriel est déjà utilisée

---

### E2 — Pages web profil, inscription, connexion, photo (15 XP)

**Pages web :**
- `GET /inscription` — Formulaire d'inscription
- `GET /connexion` — Formulaire de connexion
- `GET /profil` — Page de profil (protégée, session requise)

**Services REST :**
- `POST /api/connexion` — Authentification (ouvre une session Flask)
- `POST /api/deconnexion` — Fermeture de session
- `PUT /api/utilisateurs/<id>/etablissements` — Mise à jour des établissements surveillés
- `POST /api/utilisateurs/<id>/photo` — Upload photo de profil (jpg/png)
- `GET /api/utilisateurs/<id>/photo` — Affichage de la photo

**Comment tester :**

1. Créer un profil via `POST /api/utilisateurs` (voir E1) ou via `http://localhost:5000/inscription`
2. Se connecter sur `http://localhost:5000/connexion` avec le courriel et le mot de passe
3. La page profil `http://localhost:5000/profil` s'ouvre :
   - Modifier la liste d'établissements surveillés et cliquer « Sauvegarder »
   - Uploader une photo de profil (jpg ou png) via le formulaire
4. Se déconnecter avec le bouton « Se déconnecter »

**Tester l'API de connexion :**

```bash
curl -X POST http://localhost:5000/api/connexion \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"courriel": "marie@exemple.com", "mot_de_passe": "motdepasse123"}'
```

---

### E3 — Courriel automatique aux utilisateurs abonnés (5 XP)

**Fichier :** `mail_service.py` — fonction `notifier_abonnes()`

Lors de chaque synchronisation (A3/B1), après détection de nouveaux contrevenants,
le système envoie un courriel personnalisé à chaque utilisateur dont la liste de
surveillance contient l'établissement concerné.

**Comment tester manuellement :**

```python
# 1. Créer un utilisateur via /inscription et l'abonner à "Restaurant Test"
# 2. Simuler l'arrivée d'une nouvelle contravention pour ce restaurant :
from mail_service import notifier_nouvelles_contraventions
notifier_nouvelles_contraventions([
    {"id_poursuite": 999999, "etablissement": "Restaurant Test"}
])
# L'utilisateur abonné reçoit un courriel d'alerte avec un lien de désabonnement
```

---

### E4 — Désabonnement par lien signé dans le courriel (10 XP)

**Page web :** `GET /desabonnement?token=<token>`  
**Service REST :** `DELETE /api/desabonnement` (corps JSON : `{"token": "..."}`)  
**Fichiers :** `app.py`, `mail_service.py`, `templates/desabonnement.html`, `static/js/desabonnement.js`

Le courriel envoyé en E3 contient un lien signé (HMAC-SHA256) unique pour chaque
paire (utilisateur, établissement). Le token est encodé en base64url et signé
avec la `secret_key` de `config.yaml`.

**Flux de désabonnement :**

1. L'utilisateur clique sur le lien de désabonnement dans le courriel
2. La page `GET /desabonnement?token=XXX` affiche le nom de l'établissement et demande confirmation
3. L'utilisateur clique « Confirmer le désabonnement »
4. Une requête Ajax `DELETE /api/desabonnement` est envoyée avec le token
5. Le serveur vérifie la signature, retire l'établissement de la liste de l'utilisateur
6. Un message de succès s'affiche

**Comment tester manuellement :**

```python
# Dans un shell Python après avoir démarré l'app :
from app import generer_token_desabonnement
token = generer_token_desabonnement(1, "Restaurant Test")
print(f"http://localhost:5000/desabonnement?token={token}")
```

Ouvrir le lien généré dans un navigateur pour tester le flux complet.

---

## Structure du projet

```
projet/
├── db/
│   ├── db.sql          # Script SQL de création des tables
│   └── db.sqlite       # Base de données vide pour la remise
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── recherche.js    # Ajax A5 — recherche par dates
│       ├── restaurant.js   # Ajax A6 — recherche par restaurant
│       └── plainte.js      # Ajax D1 — formulaire de plainte
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── resultats.html
│   ├── plainte.html
│   ├── doc.html
│   └── erreur.html
├── app.py              # Application Flask — routes
├── database.py         # Couche d'accès aux données (DAL)
├── get_data.py         # Script A1 — téléchargement CSV
├── scheduler.py        # Tâche de synchronisation quotidienne (A3)
├── mail_service.py     # Service courriel (B1)
├── doc.raml            # Documentation RAML
├── config.yaml         # Configuration (SMTP, etc.)
├── requirements.txt
└── correction.md
```
