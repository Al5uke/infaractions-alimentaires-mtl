/* Soumission Ajax du formulaire de plainte / demande d'inspection (D1) */

"use strict";

/**
 * Extrait et retourne les données du formulaire sous forme d'objet.
 * @param {HTMLFormElement} formulaire - Le formulaire de plainte
 * @returns {Object} Données du formulaire
 */
function extraireDonnesFormulaire(formulaire) {
  return {
    etablissement: formulaire.etablissement.value.trim(),
    adresse: formulaire.adresse.value.trim(),
    ville: formulaire.ville.value.trim(),
    date_visite: formulaire.date_visite.value.trim(),
    prenom_client: formulaire.prenom_client.value.trim(),
    nom_client: formulaire.nom_client.value.trim(),
    description: formulaire.description.value.trim(),
  };
}

/**
 * Valide les données du formulaire côté client.
 * @param {Object} donnees - Données extraites du formulaire
 * @returns {string|null} Message d'erreur ou null si valide
 */
function validerDonnees(donnees) {
  const champsRequis = [
    ["etablissement", "Nom de l'établissement"],
    ["adresse", "Adresse"],
    ["ville", "Ville"],
    ["date_visite", "Date de visite"],
    ["prenom_client", "Prénom"],
    ["nom_client", "Nom"],
    ["description", "Description"],
  ];

  for (const [champ, label] of champsRequis) {
    if (!donnees[champ]) {
      return `Le champ « ${label} » est obligatoire.`;
    }
  }
  return null;
}

/**
 * Envoie la demande d'inspection à l'API REST.
 * @param {Object} donnees - Données de la demande
 * @returns {Promise<Object>} Réponse de l'API
 */
async function envoyerPlainte(donnees) {
  const reponse = await fetch("/api/inspections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(donnees),
  });
  const resultat = await reponse.json();
  if (!reponse.ok) {
    throw new Error(resultat.erreur || "Erreur lors de l'envoi.");
  }
  return resultat;
}

/**
 * Affiche un message de succès et réinitialise le formulaire.
 * @param {HTMLFormElement} formulaire - Le formulaire à réinitialiser
 * @param {string} message - Message de succès
 */
function afficherSucces(formulaire, message) {
  const zone = document.getElementById("message-succes");
  zone.textContent = message;
  zone.classList.remove("d-none");
  document.getElementById("message-erreur").classList.add("d-none");
  formulaire.reset();
  formulaire.querySelectorAll(".is-invalid").forEach((el) => {
    el.classList.remove("is-invalid");
  });
}

/**
 * Affiche un message d'erreur.
 * @param {string} message - Message d'erreur
 */
function afficherErreurPlainte(message) {
  const zone = document.getElementById("message-erreur");
  zone.textContent = message;
  zone.classList.remove("d-none");
  document.getElementById("message-succes").classList.add("d-none");
}

/**
 * Gestionnaire de soumission du formulaire de plainte.
 * @param {Event} evenement - Événement de soumission
 */
async function gererSoumissionPlainte(evenement) {
  evenement.preventDefault();
  const formulaire = evenement.target;
  const donnees = extraireDonnesFormulaire(formulaire);

  const erreur = validerDonnees(donnees);
  if (erreur) {
    afficherErreurPlainte(erreur);
    return;
  }

  try {
    const resultat = await envoyerPlainte(donnees);
    afficherSucces(formulaire, `Plainte soumise avec succès (no ${resultat.id}).`);
  } catch (err) {
    afficherErreurPlainte(err.message);
  }
}

document
  .getElementById("form-plainte")
  .addEventListener("submit", gererSoumissionPlainte);
