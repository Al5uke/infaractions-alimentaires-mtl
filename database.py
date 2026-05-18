"""Module d'accès aux données de la base de données SQLite.

Fournit toutes les fonctions de lecture et d'écriture pour les
contraventions alimentaires et les demandes d'inspection.
"""

import sqlite3

CHEMIN_BD = "db/db.sqlite"


def obtenir_connexion():
    """Retourne une connexion à la base de données avec Row comme type."""
    connexion = sqlite3.connect(CHEMIN_BD)
    connexion.row_factory = sqlite3.Row
    return connexion


def executer_requete(sql, parametres=()):
    """Exécute une requête SELECT et retourne les résultats en liste."""
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        curseur.execute(sql, parametres)
        return [dict(ligne) for ligne in curseur.fetchall()]
    finally:
        connexion.close()


def rechercher_par_etablissement(nom):
    """Recherche les contraventions par nom d'établissement (partiel)."""
    sql = """
        SELECT * FROM contravention
        WHERE etablissement LIKE ?
        ORDER BY date DESC
    """
    return executer_requete(sql, (f"%{nom}%",))


def rechercher_par_proprietaire(proprietaire):
    """Recherche les contraventions par nom de propriétaire (partiel)."""
    sql = """
        SELECT * FROM contravention
        WHERE proprietaire LIKE ?
        ORDER BY date DESC
    """
    return executer_requete(sql, (f"%{proprietaire}%",))


def rechercher_par_rue(rue):
    """Recherche les contraventions par rue dans le champ adresse."""
    sql = """
        SELECT * FROM contravention
        WHERE adresse LIKE ?
        ORDER BY date DESC
    """
    return executer_requete(sql, (f"%{rue}%",))


def obtenir_contraventions_par_periode(date_debut, date_fin):
    """Retourne les contraventions entre deux dates (format YYYY-MM-DD)."""
    sql = """
        SELECT etablissement, COUNT(*) as nb_contraventions
        FROM contravention
        WHERE date BETWEEN ? AND ?
        GROUP BY etablissement
        ORDER BY etablissement
    """
    return executer_requete(sql, (date_debut, date_fin))


def obtenir_statistiques():
    """Retourne les statistiques globales sur les contraventions."""
    sql = """
        SELECT
            COUNT(*)                    AS nb_contraventions,
            COUNT(DISTINCT etablissement) AS nb_etablissements,
            MAX(date)                   AS derniere_mise_a_jour
        FROM contravention
    """
    resultats = executer_requete(sql)
    return resultats[0] if resultats else {}


def obtenir_tous_etablissements():
    """Retourne la liste de tous les établissements distincts triés."""
    sql = """
        SELECT DISTINCT etablissement
        FROM contravention
        ORDER BY etablissement
    """
    return executer_requete(sql)


def obtenir_infractions_etablissement(nom):
    """Retourne toutes les infractions d'un établissement donné."""
    sql = """
        SELECT * FROM contravention
        WHERE etablissement = ?
        ORDER BY date DESC
    """
    return executer_requete(sql, (nom,))


def obtenir_etablissements_avec_nb_infractions():
    """Retourne les établissements triés par nb d'infractions décroissant."""
    sql = """
        SELECT etablissement, COUNT(*) as nb_infractions
        FROM contravention
        GROUP BY etablissement
        ORDER BY nb_infractions DESC
    """
    return executer_requete(sql)


def creer_demande_inspection(donnees):
    """Insère une demande d'inspection et retourne son identifiant."""
    sql = """
        INSERT INTO demande_inspection
            (etablissement, adresse, ville, date_visite,
             prenom_client, nom_client, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        curseur.execute(sql, (
            donnees["etablissement"],
            donnees["adresse"],
            donnees["ville"],
            donnees["date_visite"],
            donnees["prenom_client"],
            donnees["nom_client"],
            donnees["description"],
        ))
        connexion.commit()
        return curseur.lastrowid
    finally:
        connexion.close()


def supprimer_demande_inspection(id_demande):
    """Supprime une demande d'inspection par son identifiant.

    Retourne True si la suppression a réussi, False sinon.
    """
    sql = "DELETE FROM demande_inspection WHERE id = ?"
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        curseur.execute(sql, (id_demande,))
        connexion.commit()
        return curseur.rowcount > 0
    finally:
        connexion.close()


# ---------------------------------------------------------------------------
# Utilisateurs (E1–E4)
# ---------------------------------------------------------------------------

def courriel_existe(courriel):
    """Retourne True si l'adresse courriel est déjà enregistrée."""
    resultats = executer_requete(
        "SELECT id FROM utilisateur WHERE courriel = ?",
        (courriel,)
    )
    return len(resultats) > 0


def creer_utilisateur(donnees, mot_de_passe_hash):
    """Insère un utilisateur et ses établissements surveillés.

    Retourne l'identifiant du nouvel utilisateur.
    """
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        sql_ins = (
            "INSERT INTO utilisateur"
            " (nom_complet, courriel, mot_de_passe_hash)"
            " VALUES (?, ?, ?)"
        )
        curseur.execute(
            sql_ins,
            (donnees["nom_complet"], donnees["courriel"], mot_de_passe_hash),
        )
        utilisateur_id = curseur.lastrowid
        for etab in donnees.get("etablissements_surveilles", []):
            curseur.execute(
                """INSERT INTO utilisateur_etablissement
                   (utilisateur_id, etablissement) VALUES (?, ?)""",
                (utilisateur_id, etab),
            )
        connexion.commit()
        return utilisateur_id
    finally:
        connexion.close()


def obtenir_utilisateur_par_courriel(courriel):
    """Retourne un utilisateur (dict) par son courriel, ou None."""
    resultats = executer_requete(
        """SELECT id, nom_complet, courriel, mot_de_passe_hash
           FROM utilisateur WHERE courriel = ?""",
        (courriel,),
    )
    return resultats[0] if resultats else None


def obtenir_utilisateur_par_id(utilisateur_id):
    """Retourne un utilisateur (dict) par son identifiant, ou None."""
    resultats = executer_requete(
        "SELECT id, nom_complet, courriel FROM utilisateur WHERE id = ?",
        (utilisateur_id,),
    )
    return resultats[0] if resultats else None


def obtenir_etablissements_surveilles(utilisateur_id):
    """Retourne la liste des noms d'établissements surveillés."""
    resultats = executer_requete(
        """SELECT etablissement FROM utilisateur_etablissement
           WHERE utilisateur_id = ? ORDER BY etablissement""",
        (utilisateur_id,),
    )
    return [r["etablissement"] for r in resultats]


def mettre_a_jour_etablissements_surveilles(utilisateur_id, etablissements):
    """Remplace la liste complète des établissements surveillés."""
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        curseur.execute(
            "DELETE FROM utilisateur_etablissement WHERE utilisateur_id = ?",
            (utilisateur_id,),
        )
        for etab in etablissements:
            curseur.execute(
                """INSERT INTO utilisateur_etablissement
                   (utilisateur_id, etablissement) VALUES (?, ?)""",
                (utilisateur_id, etab),
            )
        connexion.commit()
    finally:
        connexion.close()


def retirer_etablissement_surveille(utilisateur_id, etablissement):
    """Supprime un établissement de la liste de surveillance.

    Retourne True si la suppression a réussi.
    """
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        curseur.execute(
            """DELETE FROM utilisateur_etablissement
               WHERE utilisateur_id = ? AND etablissement = ?""",
            (utilisateur_id, etablissement),
        )
        connexion.commit()
        return curseur.rowcount > 0
    finally:
        connexion.close()


def sauvegarder_photo_profil(utilisateur_id, donnees_photo, mime):
    """Sauvegarde la photo de profil (BLOB) dans la base de données."""
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        curseur.execute(
            "UPDATE utilisateur"
            " SET photo_profil = ?, photo_mime = ? WHERE id = ?",
            (donnees_photo, mime, utilisateur_id),
        )
        connexion.commit()
    finally:
        connexion.close()


def obtenir_photo_profil(utilisateur_id):
    """Retourne (bytes, mime_type) ou (None, None) si aucune photo."""
    connexion = obtenir_connexion()
    try:
        curseur = connexion.cursor()
        curseur.execute(
            "SELECT photo_profil, photo_mime FROM utilisateur WHERE id = ?",
            (utilisateur_id,),
        )
        ligne = curseur.fetchone()
        if ligne and ligne[0]:
            return ligne[0], ligne[1]
        return None, None
    finally:
        connexion.close()


def obtenir_utilisateurs_surveillant(etablissement):
    """Retourne les utilisateurs qui surveillent un établissement donné."""
    sql = """
        SELECT u.id, u.nom_complet, u.courriel
        FROM utilisateur u
        JOIN utilisateur_etablissement ue ON u.id = ue.utilisateur_id
        WHERE ue.etablissement = ?
    """
    return executer_requete(sql, (etablissement,))
