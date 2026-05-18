"""Module de planification des tâches de synchronisation des données (A3).

Configure et démarre un BackgroundScheduler pour synchroniser les données
de contraventions de la Ville de Montréal chaque jour à minuit.
"""

import csv
import io

from apscheduler.schedulers.background import BackgroundScheduler

import get_data
import mail_service


def synchroniser_donnees():
    """Télécharge et importe les nouvelles contraventions depuis Montréal.

    Notifie par courriel si de nouveaux établissements sont détectés.
    """
    try:
        contenu_csv = get_data.telecharger_csv(get_data.URL_DONNEES)
        nouvelles = extraire_contraventions_csv(contenu_csv)
        mail_service.notifier_nouvelles_contraventions(nouvelles)
        nb = get_data.importer_donnees(contenu_csv, get_data.CHEMIN_BD)
        print(f"Synchronisation : {nb} nouvelles contraventions ajoutées.")
    except Exception as e:
        print(f"Erreur lors de la synchronisation : {e}")


def extraire_contraventions_csv(contenu_csv):
    """Extrait les contraventions du CSV sous forme de liste de dicts."""
    lecteur = csv.DictReader(io.StringIO(contenu_csv))
    return [
        {
            "id_poursuite": int(ligne["id_poursuite"]),
            "etablissement": ligne["etablissement"],
        }
        for ligne in lecteur
    ]


def demarrer_scheduler():
    """Crée et démarre le scheduler avec la tâche de minuit."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        synchroniser_donnees,
        trigger="cron",
        hour=0,
        minute=0,
        id="sync_contraventions",
    )
    scheduler.start()
    return scheduler
