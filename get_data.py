"""Script de téléchargement et d'importation des contraventions alimentaires.

Télécharge les données CSV de la Ville de Montréal et les insère dans
la base de données SQLite existante.
"""

import csv
import io
import sqlite3

import requests

URL_DONNEES = (
    "https://data.montreal.ca/dataset/05a9e718-6810-4e73-8bb9-5955efeb91a0"
    "/resource/7f939a08-be8a-45e1-b208-d8744dca8fc6/download/violations.csv"
)
CHEMIN_BD = "db/db.sqlite"


def telecharger_csv(url):
    """Télécharge le fichier CSV depuis l'URL et retourne son contenu texte.

    Le CSV est encodé en Windows-1252 côté serveur.
    """
    reponse = requests.get(url, timeout=30)
    reponse.raise_for_status()
    return reponse.content.decode("utf-8")


def convertir_date(date_brute):
    """Convertit une date du format YYYYMMDD vers YYYY-MM-DD.

    Retourne None si la date est absente ou invalide.
    """
    if not date_brute or len(date_brute) != 8:
        return None
    return f"{date_brute[:4]}-{date_brute[4:6]}-{date_brute[6:]}"


def construire_tuple(ligne):
    """Construit le tuple de valeurs à insérer à partir d'une ligne du CSV."""
    return (
        int(ligne["id_poursuite"]),
        int(ligne["business_id"]) if ligne["business_id"] else None,
        convertir_date(ligne["date"]),
        ligne["description"],
        ligne["adresse"],
        convertir_date(ligne["date_jugement"]),
        ligne["etablissement"],
        int(ligne["montant"]) if ligne["montant"] else None,
        ligne["proprietaire"],
        ligne["ville"],
        ligne["statut"],
        convertir_date(ligne["date_statut"]),
        ligne["categorie"],
    )


def inserer_contravention(curseur, ligne):
    """Insère une contravention si elle n'existe pas déjà."""
    sql = """
        INSERT OR IGNORE INTO contravention (
            id_poursuite, business_id, date, description, adresse,
            date_jugement, etablissement, montant, proprietaire,
            ville, statut, date_statut, categorie
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    curseur.execute(sql, construire_tuple(ligne))


def importer_donnees(contenu_csv, chemin_bd):
    """Importe toutes les contraventions du CSV dans la base de données.

    Retourne le nombre de nouvelles contraventions insérées.
    """
    lecteur = csv.DictReader(io.StringIO(contenu_csv))
    connexion = sqlite3.connect(chemin_bd)
    nb_inseres = 0
    try:
        curseur = connexion.cursor()
        for ligne in lecteur:
            inserer_contravention(curseur, ligne)
            nb_inseres += curseur.rowcount
        connexion.commit()
    finally:
        connexion.close()
    return nb_inseres


def main():
    """Point d'entrée principal du script d'importation."""
    print("Téléchargement des données en cours...")
    contenu_csv = telecharger_csv(URL_DONNEES)
    print("Importation dans la base de données...")
    nb_inseres = importer_donnees(contenu_csv, CHEMIN_BD)
    print(f"Importation terminée : {nb_inseres} nouvelles ajoutées.")


if __name__ == "__main__":
    main()
