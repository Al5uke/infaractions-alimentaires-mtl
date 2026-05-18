"""Application Flask de gestion des contraventions alimentaires de Montréal.

Point d'entrée principal de l'application. Définit les routes web et les
services REST. La logique d'accès aux données est déléguée à database.py.
"""

import base64
import csv
import hmac
import io
import hashlib
from xml.etree.ElementTree import Element, SubElement, tostring

import jsonschema
import yaml
from flask import Flask, Response, jsonify, redirect, session
from flask import render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import database
import scheduler

app = Flask(__name__)

with open("config.yaml", "r", encoding="utf-8") as _f:
    _cfg = yaml.safe_load(_f)
app.secret_key = _cfg.get("secret_key", "changeme")

TYPES_RECHERCHE_VALIDES = ["etablissement", "proprietaire", "rue"]

SCHEMA_INSPECTION = {
    "type": "object",
    "required": [
        "etablissement", "adresse", "ville", "date_visite",
        "prenom_client", "nom_client", "description",
    ],
    "properties": {
        "etablissement": {"type": "string", "minLength": 1},
        "adresse": {"type": "string", "minLength": 1},
        "ville": {"type": "string", "minLength": 1},
        "date_visite": {
            "type": "string",
            "pattern": r"^\d{4}-\d{2}-\d{2}$",
        },
        "prenom_client": {"type": "string", "minLength": 1},
        "nom_client": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

SCHEMA_UTILISATEUR = {
    "type": "object",
    "required": [
        "nom_complet", "courriel",
        "etablissements_surveilles", "mot_de_passe",
    ],
    "properties": {
        "nom_complet": {"type": "string", "minLength": 1},
        "courriel": {
            "type": "string",
            "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        },
        "etablissements_surveilles": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "mot_de_passe": {"type": "string", "minLength": 6},
    },
    "additionalProperties": False,
}

MIMES_PHOTO_VALIDES = {"image/jpeg", "image/png"}

scheduler.demarrer_scheduler()


# ---------------------------------------------------------------------------
# Utilitaires de token (E4)
# ---------------------------------------------------------------------------

def _signer(donnees):
    """Retourne une signature HMAC-SHA256 en hexadécimal."""
    return hmac.new(
        app.secret_key.encode(),
        donnees.encode(),
        hashlib.sha256,
    ).hexdigest()


def generer_token_desabonnement(utilisateur_id, etablissement):
    """Génère un token signé encodant (utilisateur_id, etablissement)."""
    payload = base64.urlsafe_b64encode(
        f"{utilisateur_id}:{etablissement}".encode()
    ).decode()
    return f"{payload}.{_signer(payload)}"


def verifier_token_desabonnement(token):
    """Vérifie et décode un token de désabonnement.

    Retourne (utilisateur_id, etablissement) ou (None, None) si invalide.
    """
    try:
        payload, signature = token.rsplit(".", 1)
        if not hmac.compare_digest(signature, _signer(payload)):
            return None, None
        donnees = base64.urlsafe_b64decode(payload.encode()).decode()
        uid_str, etablissement = donnees.split(":", 1)
        return int(uid_str), etablissement
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# Pages web
# ---------------------------------------------------------------------------

@app.route("/")
def afficher_accueil():
    """Affiche la page d'accueil avec les formulaires de recherche."""
    etablissements = database.obtenir_tous_etablissements()
    stats = database.obtenir_statistiques()
    return render_template(
        "index.html",
        etablissements=etablissements,
        stats=stats,
    )


@app.route("/recherche", methods=["POST"])
def traiter_recherche():
    """Valide le formulaire de recherche et redirige vers les résultats."""
    type_recherche = request.form.get("type_recherche", "").strip()
    valeur = request.form.get("valeur", "").strip()

    if not type_recherche or not valeur:
        etablissements = database.obtenir_tous_etablissements()
        return render_template(
            "index.html",
            erreur="Veuillez remplir tous les champs.",
            etablissements=etablissements,
        )

    if type_recherche not in TYPES_RECHERCHE_VALIDES:
        etablissements = database.obtenir_tous_etablissements()
        return render_template(
            "index.html",
            erreur="Type de recherche invalide.",
            etablissements=etablissements,
        )

    return redirect(url_for(
        "afficher_resultats",
        type=type_recherche,
        valeur=valeur,
    ))


@app.route("/resultats")
def afficher_resultats():
    """Affiche les résultats de la recherche de contraventions."""
    type_recherche = request.args.get("type", "").strip()
    valeur = request.args.get("valeur", "").strip()

    if not type_recherche or not valeur:
        return redirect(url_for("afficher_accueil"))

    contraventions = recuperer_contraventions(type_recherche, valeur)
    return render_template(
        "resultats.html",
        contraventions=contraventions,
        type_recherche=type_recherche,
        valeur=valeur,
    )


def recuperer_contraventions(type_recherche, valeur):
    """Appelle la fonction de recherche appropriée selon le type."""
    if type_recherche == "etablissement":
        return database.rechercher_par_etablissement(valeur)
    if type_recherche == "proprietaire":
        return database.rechercher_par_proprietaire(valeur)
    if type_recherche == "rue":
        return database.rechercher_par_rue(valeur)
    return []


@app.route("/plainte")
def afficher_plainte():
    """Affiche le formulaire de demande d'inspection."""
    return render_template("plainte.html")


# ---------------------------------------------------------------------------
# Pages web — Authentification et profil (E2)
# ---------------------------------------------------------------------------

@app.route("/inscription")
def afficher_inscription():
    """Affiche la page d'inscription."""
    if session.get("utilisateur_id"):
        return redirect(url_for("afficher_profil"))
    return render_template("inscription.html")


@app.route("/connexion")
def afficher_connexion():
    """Affiche la page de connexion."""
    if session.get("utilisateur_id"):
        return redirect(url_for("afficher_profil"))
    return render_template("connexion.html")


@app.route("/profil")
def afficher_profil():
    """Affiche la page de profil de l'utilisateur connecté."""
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        return redirect(url_for("afficher_connexion"))
    utilisateur = database.obtenir_utilisateur_par_id(utilisateur_id)
    if not utilisateur:
        session.clear()
        return redirect(url_for("afficher_connexion"))
    surveilles = database.obtenir_etablissements_surveilles(utilisateur_id)
    tous = database.obtenir_tous_etablissements()
    return render_template(
        "profil.html",
        utilisateur=utilisateur,
        surveilles=surveilles,
        tous_etablissements=tous,
    )


@app.route("/desabonnement")
def afficher_desabonnement():
    """Affiche la page de confirmation de désabonnement (E4)."""
    token = request.args.get("token", "").strip()
    if not token:
        return render_template("erreur.html", code=400,
                               message="Token manquant."), 400
    uid, etablissement = verifier_token_desabonnement(token)
    if uid is None:
        return render_template("erreur.html", code=400,
                               message="Lien de désabonnement invalide."), 400
    return render_template(
        "desabonnement.html",
        token=token,
        etablissement=etablissement,
    )


# ---------------------------------------------------------------------------
# Services REST — Contraventions
# ---------------------------------------------------------------------------

@app.route("/contrevenants")
def lister_contrevenants_par_periode():
    """Retourne les contraventions entre deux dates en JSON.

    Paramètres : du (date début) et au (date fin) en format YYYY-MM-DD.
    """
    date_debut = request.args.get("du", "").strip()
    date_fin = request.args.get("au", "").strip()

    if not date_debut or not date_fin:
        return jsonify({"erreur": "Paramètres 'du' et 'au' requis."}), 400

    if date_debut > date_fin:
        msg = "La date de début doit précéder la date de fin."
        return jsonify({"erreur": msg}), 400

    resultats = database.obtenir_contraventions_par_periode(
        date_debut, date_fin
    )
    return jsonify(resultats)


@app.route("/api/etablissement/<nom>")
def lister_infractions_etablissement(nom):
    """Retourne les infractions d'un établissement donné en JSON."""
    infractions = database.obtenir_infractions_etablissement(nom)
    if not infractions:
        return jsonify({"erreur": "Établissement non trouvé."}), 404
    return jsonify(infractions)


# ---------------------------------------------------------------------------
# Services REST — Établissements (C1/C2/C3)
# ---------------------------------------------------------------------------

@app.route("/api/etablissements")
def lister_etablissements():
    """Retourne les établissements avec leur nombre d'infractions (JSON)."""
    etablissements = database.obtenir_etablissements_avec_nb_infractions()
    return jsonify(etablissements)


@app.route("/api/etablissements.xml")
def lister_etablissements_xml():
    """Retourne les établissements avec leur nombre d'infractions (XML)."""
    etablissements = database.obtenir_etablissements_avec_nb_infractions()
    contenu_xml = construire_xml_etablissements(etablissements)
    return Response(contenu_xml, mimetype="application/xml; charset=utf-8")


@app.route("/api/etablissements.csv")
def lister_etablissements_csv():
    """Retourne les établissements avec leur nombre d'infractions (CSV)."""
    etablissements = database.obtenir_etablissements_avec_nb_infractions()
    contenu_csv = construire_csv_etablissements(etablissements)
    return Response(
        contenu_csv,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=etablissements.csv"
        },
    )


def construire_xml_etablissements(etablissements):
    """Construit le document XML pour la liste des établissements."""
    racine = Element("etablissements")
    for e in etablissements:
        noeud = SubElement(racine, "etablissement")
        SubElement(noeud, "nom").text = e["etablissement"]
        SubElement(noeud, "nb_infractions").text = str(e["nb_infractions"])
    declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    return declaration + tostring(racine, encoding="unicode")


def construire_csv_etablissements(etablissements):
    """Construit le contenu CSV pour la liste des établissements."""
    sortie = io.StringIO()
    writer = csv.writer(sortie)
    writer.writerow(["etablissement", "nb_infractions"])
    for e in etablissements:
        writer.writerow([e["etablissement"], e["nb_infractions"]])
    return sortie.getvalue()


# ---------------------------------------------------------------------------
# Services REST — Demandes d'inspection (D1/D2)
# ---------------------------------------------------------------------------

@app.route("/api/inspections", methods=["POST"])
def creer_inspection():
    """Crée une demande d'inspection après validation JSON."""
    donnees = request.get_json(silent=True)

    if not donnees:
        return jsonify({"erreur": "Corps JSON requis."}), 400

    erreur = valider_schema_inspection(donnees)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    id_demande = database.creer_demande_inspection(donnees)
    return jsonify({
        "id": id_demande,
        "message": "Demande créée avec succès.",
    }), 201


@app.route("/api/inspections/<int:id_demande>", methods=["DELETE"])
def supprimer_inspection(id_demande):
    """Supprime une demande d'inspection par son identifiant."""
    supprime = database.supprimer_demande_inspection(id_demande)
    if not supprime:
        return jsonify({"erreur": "Demande non trouvée."}), 404
    return jsonify({"message": "Demande supprimée avec succès."})


def valider_schema_inspection(donnees):
    """Valide les données d'inspection avec json-schema.

    Retourne un message d'erreur si invalide, None sinon.
    """
    try:
        jsonschema.validate(instance=donnees, schema=SCHEMA_INSPECTION)
        return None
    except jsonschema.ValidationError as e:
        return e.message


# ---------------------------------------------------------------------------
# Services REST — Utilisateurs (E1/E2)
# ---------------------------------------------------------------------------

@app.route("/api/utilisateurs", methods=["POST"])
def creer_utilisateur():
    """Crée un profil utilisateur après validation JSON (E1)."""
    donnees = request.get_json(silent=True)

    if not donnees:
        return jsonify({"erreur": "Corps JSON requis."}), 400

    erreur = valider_schema_utilisateur(donnees)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    if database.courriel_existe(donnees["courriel"]):
        msg = "Cette adresse courriel est déjà utilisée."
        return jsonify({"erreur": msg}), 409

    hash_mdp = generate_password_hash(donnees["mot_de_passe"])
    utilisateur_id = database.creer_utilisateur(donnees, hash_mdp)
    return jsonify({
        "id": utilisateur_id,
        "message": "Profil créé avec succès.",
    }), 201


@app.route("/api/connexion", methods=["POST"])
def connexion():
    """Authentifie un utilisateur et ouvre une session (E2)."""
    donnees = request.get_json(silent=True)
    if not donnees or not donnees.get("courriel") \
            or not donnees.get("mot_de_passe"):
        return jsonify({"erreur": "Courriel et mot de passe requis."}), 400

    utilisateur = database.obtenir_utilisateur_par_courriel(
        donnees["courriel"]
    )
    if not utilisateur or not check_password_hash(
        utilisateur["mot_de_passe_hash"], donnees["mot_de_passe"]
    ):
        return jsonify({"erreur": "Identifiants incorrects."}), 401

    session["utilisateur_id"] = utilisateur["id"]
    return jsonify({
        "id": utilisateur["id"],
        "nom_complet": utilisateur["nom_complet"],
        "message": "Connexion réussie.",
    })


@app.route("/api/deconnexion", methods=["POST"])
def deconnexion():
    """Ferme la session de l'utilisateur (E2)."""
    session.clear()
    return jsonify({"message": "Déconnexion réussie."})


@app.route("/api/utilisateurs/<int:utilisateur_id>/etablissements",
           methods=["PUT"])
def mettre_a_jour_etablissements(utilisateur_id):
    """Remplace la liste d'établissements surveillés (E2)."""
    if session.get("utilisateur_id") != utilisateur_id:
        return jsonify({"erreur": "Non autorisé."}), 403

    donnees = request.get_json(silent=True)
    if donnees is None or "etablissements" not in donnees:
        return jsonify({"erreur": "Champ 'etablissements' requis."}), 400

    if not isinstance(donnees["etablissements"], list):
        msg = "'etablissements' doit être une liste."
        return jsonify({"erreur": msg}), 400

    database.mettre_a_jour_etablissements_surveilles(
        utilisateur_id, donnees["etablissements"]
    )
    return jsonify({"message": "Liste mise à jour."})


@app.route("/api/utilisateurs/<int:utilisateur_id>/photo", methods=["POST"])
def televerser_photo(utilisateur_id):
    """Sauvegarde une photo de profil jpg/png dans la base (E2)."""
    if session.get("utilisateur_id") != utilisateur_id:
        return jsonify({"erreur": "Non autorisé."}), 403

    if "photo" not in request.files:
        return jsonify({"erreur": "Fichier 'photo' requis."}), 400

    fichier = request.files["photo"]
    mime = fichier.mimetype
    if mime not in MIMES_PHOTO_VALIDES:
        msg = "Format non supporté. Utilisez jpg ou png."
        return jsonify({"erreur": msg}), 400

    database.sauvegarder_photo_profil(utilisateur_id, fichier.read(), mime)
    return jsonify({"message": "Photo mise à jour."})


@app.route("/api/utilisateurs/<int:utilisateur_id>/photo", methods=["GET"])
def obtenir_photo(utilisateur_id):
    """Retourne la photo de profil d'un utilisateur (E2)."""
    donnees, mime = database.obtenir_photo_profil(utilisateur_id)
    if donnees is None:
        return jsonify({"erreur": "Aucune photo."}), 404
    return Response(donnees, mimetype=mime)


# ---------------------------------------------------------------------------
# Services REST — Désabonnement (E4)
# ---------------------------------------------------------------------------

@app.route("/api/desabonnement", methods=["DELETE"])
def traiter_desabonnement():
    """Supprime un établissement de la liste de surveillance via token (E4)."""
    donnees = request.get_json(silent=True)
    if not donnees or not donnees.get("token"):
        return jsonify({"erreur": "Token requis."}), 400

    uid, etablissement = verifier_token_desabonnement(donnees["token"])
    if uid is None:
        return jsonify({"erreur": "Token invalide ou expiré."}), 400

    retire = database.retirer_etablissement_surveille(uid, etablissement)
    if not retire:
        return jsonify({"erreur": "Abonnement introuvable."}), 404

    return jsonify({"message": f"Désabonné de « {etablissement} »."})


def valider_schema_utilisateur(donnees):
    """Valide les données utilisateur avec json-schema.

    Retourne un message d'erreur si invalide, None sinon.
    """
    try:
        jsonschema.validate(instance=donnees, schema=SCHEMA_UTILISATEUR)
        return None
    except jsonschema.ValidationError as e:
        return e.message


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

@app.route("/doc")
def afficher_documentation():
    """Affiche la documentation RAML des services REST."""
    return render_template("doc.html")


# ---------------------------------------------------------------------------
# Gestion des erreurs
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def page_non_trouvee(e):
    """Retourne une page d'erreur 404."""
    return render_template("erreur.html", code=404,
                           message="Page non trouvée."), 404


@app.errorhandler(500)
def erreur_serveur(e):
    """Retourne une page d'erreur 500."""
    return render_template("erreur.html", code=500,
                           message="Erreur interne du serveur."), 500


if __name__ == "__main__":
    app.run(debug=True)
