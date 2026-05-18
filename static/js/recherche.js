/* Recherche Ajax par période de dates (A5) */

"use strict";

/**
 * Envoie une requête Ajax pour obtenir les contrevenants entre deux dates.
 * @param {string} dateDebut - Date de début (YYYY-MM-DD)
 * @param {string} dateFin - Date de fin (YYYY-MM-DD)
 * @returns {Promise<Array>} Liste des contrevenants
 */
async function fetchContrevenants(dateDebut, dateFin) {
  const url = `/contrevenants?du=${dateDebut}&au=${dateFin}`;
  const reponse = await fetch(url);
  if (!reponse.ok) {
    const erreur = await reponse.json();
    throw new Error(erreur.erreur || "Erreur lors de la requête.");
  }
  return reponse.json();
}

/**
 * Construit une ligne de tableau pour un contrevenant.
 * @param {Object} contrevenant - Objet avec etablissement et nb_contraventions
 * @returns {HTMLTableRowElement} Élément tr
 */
function creerLigneTableau(contrevenant) {
  const tr = document.createElement("tr");
  const tdNom = document.createElement("td");
  const tdNb = document.createElement("td");
  tdNom.textContent = contrevenant.etablissement;
  tdNb.textContent = contrevenant.nb_contraventions;
  tr.appendChild(tdNom);
  tr.appendChild(tdNb);
  return tr;
}

/**
 * Affiche les résultats dans le tableau HTML.
 * @param {Array} contrevenants - Liste des contrevenants
 */
function afficherResultats(contrevenants) {
  const corps = document.getElementById("corps-tableau-dates");
  const section = document.getElementById("resultats-dates");
  const aucunResultat = document.getElementById("aucun-resultat-dates");

  corps.innerHTML = "";
  section.classList.remove("d-none");

  if (contrevenants.length === 0) {
    aucunResultat.classList.remove("d-none");
    return;
  }

  aucunResultat.classList.add("d-none");
  contrevenants.forEach((c) => corps.appendChild(creerLigneTableau(c)));
}

/**
 * Affiche un message d'erreur dans la zone prévue.
 * @param {string} message - Message d'erreur à afficher
 */
function afficherErreurDates(message) {
  const zone = document.getElementById("erreur-dates");
  zone.textContent = message;
  zone.classList.remove("d-none");
}

/**
 * Efface le message d'erreur.
 */
function effacerErreurDates() {
  const zone = document.getElementById("erreur-dates");
  zone.classList.add("d-none");
}

/**
 * Affiche ou masque le spinner de chargement.
 * @param {boolean} visible - true pour afficher, false pour masquer
 */
function toggleSpinnerDates(visible) {
  const spinner = document.getElementById("spinner-dates");
  spinner.classList.toggle("d-none", !visible);
}

/**
 * Gestionnaire de soumission du formulaire de recherche par dates.
 * @param {Event} evenement - Événement de soumission du formulaire
 */
async function gererSoumissionDates(evenement) {
  evenement.preventDefault();
  effacerErreurDates();

  const dateDebut = document.getElementById("date-debut").value;
  const dateFin = document.getElementById("date-fin").value;

  if (!dateDebut || !dateFin) {
    afficherErreurDates("Veuillez saisir les deux dates.");
    return;
  }

  if (dateDebut > dateFin) {
    afficherErreurDates("La date de début doit précéder la date de fin.");
    return;
  }

  toggleSpinnerDates(true);
  try {
    const contrevenants = await fetchContrevenants(dateDebut, dateFin);
    afficherResultats(contrevenants);
  } catch (erreur) {
    afficherErreurDates(erreur.message);
  } finally {
    toggleSpinnerDates(false);
  }
}

document
  .getElementById("form-recherche-dates")
  .addEventListener("submit", gererSoumissionDates);
