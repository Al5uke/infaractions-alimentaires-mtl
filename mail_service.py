"""Service d'envoi de courriels pour les nouvelles contraventions (B1/E3).

Détecte les nouvelles contraventions depuis la dernière synchronisation
et envoie une notification par courriel à l'adresse configurée (B1) ainsi
qu'aux utilisateurs abonnés aux établissements concernés (E3/E4).
"""

import base64
import hashlib
import hmac
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml

CHEMIN_CONFIG = "config.yaml"
CHEMIN_BD = "db/db.sqlite"


def charger_configuration():
    """Charge et retourne la configuration depuis config.yaml."""
    with open(CHEMIN_CONFIG, "r", encoding="utf-8") as fichier:
        return yaml.safe_load(fichier)


def obtenir_ids_existants(connexion):
    """Retourne l'ensemble des id_poursuite déjà présents dans la base."""
    curseur = connexion.cursor()
    curseur.execute("SELECT id_poursuite FROM contravention")
    return {ligne[0] for ligne in curseur.fetchall()}


def detecter_nouveaux_etablissements(anciens_ids, nouvelles_contraventions):
    """Retourne la liste sans doublon des nouveaux établissements.

    Compare les identifiants existants avec les nouvelles données.
    """
    nouveaux = []
    vus = set()
    for c in nouvelles_contraventions:
        id_p = c.get("id_poursuite")
        nom = c.get("etablissement", "")
        if id_p not in anciens_ids and nom not in vus:
            nouveaux.append(nom)
            vus.add(nom)
    return nouveaux


def construire_courriel(
    config, expediteur, destinataire, sujet, corps_html, corps_texte
):
    """Construit un courriel MIME multipart."""
    message = MIMEMultipart("alternative")
    message["Subject"] = sujet
    message["From"] = expediteur
    message["To"] = destinataire
    message.attach(MIMEText(corps_texte, "plain", "utf-8"))
    message.attach(MIMEText(corps_html, "html", "utf-8"))
    return message


def envoyer_courriel(config, message):
    """Envoie le courriel via SMTP en utilisant la configuration fournie."""
    conf = config["courriel"]
    with smtplib.SMTP(conf["serveur_smtp"], conf["port_smtp"]) as serveur:
        serveur.starttls()
        serveur.login(conf["expediteur"], conf["mot_de_passe"])
        serveur.send_message(message)


# ---------------------------------------------------------------------------
# B1 — Notification à l'adresse configurée
# ---------------------------------------------------------------------------

def notifier_nouvelles_contraventions(nouvelles_contraventions):
    """Envoie un courriel si de nouvelles contraventions ont été détectées.

    Accepte une liste de dicts représentant les nouvelles contraventions.
    Appelle également la notification aux abonnés (E3).
    """
    connexion = sqlite3.connect(CHEMIN_BD)
    try:
        anciens_ids = obtenir_ids_existants(connexion)
    finally:
        connexion.close()

    etablissements = detecter_nouveaux_etablissements(
        anciens_ids, nouvelles_contraventions
    )

    if not etablissements:
        return

    try:
        config = charger_configuration()
        conf = config["courriel"]
        liste_html = "".join(f"<li>{e}</li>" for e in etablissements)
        corps_html = (
            "<h2>Nouveaux établissements contrevenants</h2>"
            f"<ul>{liste_html}</ul>"
        )
        corps_texte = "Nouveaux contrevenants :\n" + "\n".join(
            f"- {e}" for e in etablissements
        )
        message = construire_courriel(
            config,
            conf["expediteur"],
            conf["destinataire"],
            "Nouvelles contraventions alimentaires — Montréal",
            corps_html,
            corps_texte,
        )
        envoyer_courriel(config, message)
        nb = len(etablissements)
        print(f"Courriel B1 envoyé : {nb} nouveaux contrevenants.")
    except Exception as e:
        print(f"Erreur d'envoi du courriel B1 : {e}")

    notifier_abonnes(etablissements)


# ---------------------------------------------------------------------------
# E3/E4 — Notification aux utilisateurs abonnés
# ---------------------------------------------------------------------------

def _generer_token(utilisateur_id, etablissement, secret_key):
    """Génère un token HMAC signé pour le désabonnement."""
    payload = base64.urlsafe_b64encode(
        f"{utilisateur_id}:{etablissement}".encode()
    ).decode()
    signature = hmac.new(
        secret_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def obtenir_abonnes_par_etablissement(connexion, etablissement):
    """Retourne les utilisateurs abonnés à un établissement."""
    curseur = connexion.cursor()
    curseur.execute(
        """SELECT u.id, u.nom_complet, u.courriel
           FROM utilisateur u
           JOIN utilisateur_etablissement ue ON u.id = ue.utilisateur_id
           WHERE ue.etablissement = ?""",
        (etablissement,),
    )
    return curseur.fetchall()


def notifier_abonnes(nouveaux_etablissements):
    """Envoie un courriel aux abonnés des nouveaux contrevenants (E3/E4)."""
    if not nouveaux_etablissements:
        return

    try:
        config = charger_configuration()
        conf = config["courriel"]
        secret_key = config.get("secret_key", "changeme")
    except Exception as e:
        print(f"Erreur de configuration E3 : {e}")
        return

    connexion = sqlite3.connect(CHEMIN_BD)
    try:
        for etablissement in nouveaux_etablissements:
            abonnes = obtenir_abonnes_par_etablissement(
                connexion, etablissement
            )
            for abonne in abonnes:
                uid, nom, courriel_dest = abonne[0], abonne[1], abonne[2]
                token = _generer_token(uid, etablissement, secret_key)
                _envoyer_courriel_abonne(
                    config, conf, nom, courriel_dest, etablissement, token
                )
    except Exception as e:
        print(f"Erreur notification abonnés E3 : {e}")
    finally:
        connexion.close()


def _envoyer_courriel_abonne(
    config, conf, nom, courriel_dest, etablissement, token
):
    """Envoie le courriel d'alerte avec le lien de désabonnement."""
    lien_desabonnement = (
        f"http://localhost:5000/desabonnement?token={token}"
    )
    corps_html = f"""
    <p>Bonjour {nom},</p>
    <p>
      L'établissement <strong>{etablissement}</strong> que vous surveillez
      vient de recevoir une nouvelle contravention alimentaire à Montréal.
    </p>
    <p>
      Consultez les détails sur
      <a href="http://localhost:5000">notre site</a>.
    </p>
    <hr>
    <p style="font-size:0.85em; color:#888;">
      Pour ne plus recevoir d'alertes pour cet établissement,
      <a href="{lien_desabonnement}">cliquez ici pour vous désabonner</a>.
    </p>
    """
    corps_texte = (
        f"Bonjour {nom},\n\n"
        f"L'établissement « {etablissement} » que vous surveillez "
        f"vient de recevoir une nouvelle contravention à Montréal.\n\n"
        f"Consultez les détails sur http://localhost:5000\n\n"
        f"Pour vous désabonner : {lien_desabonnement}"
    )
    try:
        message = construire_courriel(
            config,
            conf["expediteur"],
            courriel_dest,
            f"Alerte : nouvelle contravention — {etablissement}",
            corps_html,
            corps_texte,
        )
        envoyer_courriel(config, message)
        print(f"Courriel E3 envoyé à {courriel_dest} ({etablissement}).")
    except Exception as e:
        print(f"Erreur envoi E3 à {courriel_dest} : {e}")
