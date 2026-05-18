/* Recherche Ajax des infractions d'un restaurant (A6) */

"use strict";

/**
 * Récupère les infractions d'un établissement via l'API REST.
 * @param {string} nomEtablissement - Nom exact de l'établissement
 * @returns {Promise<Array>} Liste des infractions
 */
async function fetchInfractionsRestaurant(nomEtablissement) {
  const url = `/api/etablissement/${encodeURIComponent(nomEtablissement)}`;
  const reponse = await fetch(url);
  if (!reponse.ok) {
    const erreur = await reponse.json();
    throw new Error(erreur.erreur || "Erreur lors de la requête.");
  }
  return reponse.json();
}

/**
 * Construit une carte HTML pour une infraction.
 * @param {Object} infraction - Objet contenant les données de l'infraction
 * @returns {HTMLElement} Élément article
 */
function creerCarteInfraction(infraction) {
  const article = document.createElement("article");
  article.className = "card mb-2";

  const corps = document.createElement("div");
  corps.className = "card-body";

  const champs = [
    ["Date", infraction.date],
    ["Description", infraction.description],
    ["Montant", `${infraction.montant} $`],
    ["Statut", infraction.statut],
    ["Adresse", infraction.adresse],
    ["Catégorie", infraction.categorie],
  ];

  const dl = document.createElement("dl");
  dl.className = "row mb-0 small";

  champs.forEach(([label, valeur]) => {
    const dt = document.createElement("dt");
    dt.className = "col-sm-3";
    dt.textContent = label;

    const dd = document.createElement("dd");
    dd.className = "col-sm-9";
    dd.textContent = valeur || "—";

    dl.appendChild(dt);
    dl.appendChild(dd);
  });

  corps.appendChild(dl);
  article.appendChild(corps);
  return article;
}

/**
 * Affiche la liste des infractions dans la section prévue.
 * @param {string} nomEtablissement - Nom de l'établissement
 * @param {Array} infractions - Liste des infractions
 */
function afficherInfractions(nomEtablissement, infractions) {
  const section = document.getElementById("resultats-restaurant");
  const titre = document.getElementById("titre-restaurant");
  const liste = document.getElementById("liste-infractions");

  liste.innerHTML = "";
  titre.textContent = `${infractions.length} infraction(s) — ${nomEtablissement}`;
  section.classList.remove("d-none");

  if (infractions.length === 0) {
    liste.textContent = "Aucune infraction trouvée.";
    return;
  }

  infractions.forEach((inf) => liste.appendChild(creerCarteInfraction(inf)));
}

/**
 * Affiche un message d'erreur dans la zone prévue.
 * @param {string} message - Message à afficher
 */
function afficherErreurRestaurant(message) {
  const zone = document.getElementById("erreur-restaurant");
  zone.textContent = message;
  zone.classList.remove("d-none");
}

/**
 * Efface le message d'erreur.
 */
function effacerErreurRestaurant() {
  const zone = document.getElementById("erreur-restaurant");
  zone.classList.add("d-none");
}

/**
 * Affiche ou masque le spinner de chargement.
 * @param {boolean} visible - true pour afficher, false pour masquer
 */
function toggleSpinnerRestaurant(visible) {
  const spinner = document.getElementById("spinner-restaurant");
  spinner.classList.toggle("d-none", !visible);
}

/**
 * Gestionnaire de soumission du formulaire de recherche par restaurant.
 * @param {Event} evenement - Événement de soumission
 */
async function gererSoumissionRestaurant(evenement) {
  evenement.preventDefault();
  effacerErreurRestaurant();

  const select = document.getElementById("select-restaurant");
  const nomEtablissement = select.value;

  if (!nomEtablissement) {
    afficherErreurRestaurant("Veuillez sélectionner un établissement.");
    return;
  }

  toggleSpinnerRestaurant(true);
  try {
    const infractions = await fetchInfractionsRestaurant(nomEtablissement);
    afficherInfractions(nomEtablissement, infractions);
  } catch (erreur) {
    afficherErreurRestaurant(erreur.message);
  } finally {
    toggleSpinnerRestaurant(false);
  }
}

document
  .getElementById("form-recherche-restaurant")
  .addEventListener("submit", gererSoumissionRestaurant);
