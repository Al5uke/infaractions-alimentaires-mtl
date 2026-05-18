"use strict";

// ---- Déconnexion ----

document.getElementById("btn-deconnexion").addEventListener("click", async () => {
    await fetch("/api/deconnexion", {method: "POST"});
    window.location.href = "/connexion";
});

// ---- Photo de profil ----

document.getElementById("form-photo").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msgPhoto = document.getElementById("msg-photo");
    msgPhoto.className = "alert d-none mb-2";

    const fichier = document.getElementById("input-photo").files[0];
    if (!fichier) {
        afficherMsg(msgPhoto, "danger", "Veuillez sélectionner un fichier.");
        return;
    }

    const formData = new FormData();
    formData.append("photo", fichier);

    try {
        const reponse = await fetch(`/api/utilisateurs/${UTILISATEUR_ID}/photo`, {
            method: "POST",
            body: formData,
        });
        const json = await reponse.json();

        if (reponse.ok) {
            afficherMsg(msgPhoto, "success", "Photo mise à jour.");
            document.getElementById("avatar").src =
                `/api/utilisateurs/${UTILISATEUR_ID}/photo?t=${Date.now()}`;
        } else {
            afficherMsg(msgPhoto, "danger", json.erreur || "Erreur lors de l'envoi.");
        }
    } catch {
        afficherMsg(msgPhoto, "danger", "Impossible de contacter le serveur.");
    }
});

// ---- Établissements surveillés ----

let listeSurveillee = Array.from(
    document.querySelectorAll("#liste-surveilles li[data-etablissement]")
).map(li => li.dataset.etablissement);

document.getElementById("btn-ajouter").addEventListener("click", () => {
    const select = document.getElementById("select-etab");
    const nom = select.value;
    if (!nom || listeSurveillee.includes(nom)) return;
    listeSurveillee.push(nom);
    ajouterLigneEtab(nom);
    cacherMsgVide();
    select.value = "";
});

function ajouterLigneEtab(nom) {
    let liste = document.getElementById("liste-surveilles");
    if (!liste) {
        liste = document.createElement("ul");
        liste.id = "liste-surveilles";
        liste.className = "list-group";
        document.getElementById("btn-sauvegarder").before(liste);
    }
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";
    li.dataset.etablissement = nom;
    li.textContent = nom;
    const btn = document.createElement("button");
    btn.className = "btn btn-sm btn-outline-danger btn-retirer";
    btn.dataset.nom = nom;
    btn.textContent = "Retirer";
    btn.addEventListener("click", () => retirerEtab(nom, li));
    li.appendChild(btn);
    liste.appendChild(li);
}

function retirerEtab(nom, li) {
    listeSurveillee = listeSurveillee.filter(e => e !== nom);
    li.remove();
    if (listeSurveillee.length === 0) afficherMsgVide();
}

function cacherMsgVide() {
    const el = document.getElementById("msg-vide");
    if (el) el.classList.add("d-none");
}

function afficherMsgVide() {
    const el = document.getElementById("msg-vide");
    if (el) el.classList.remove("d-none");
}

document.querySelectorAll(".btn-retirer").forEach(btn => {
    btn.addEventListener("click", () => {
        const nom = btn.dataset.nom;
        const li = btn.closest("li");
        retirerEtab(nom, li);
    });
});

document.getElementById("btn-sauvegarder").addEventListener("click", async () => {
    const msgEtab = document.getElementById("msg-etab");
    msgEtab.className = "alert d-none mb-3";

    try {
        const reponse = await fetch(`/api/utilisateurs/${UTILISATEUR_ID}/etablissements`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({etablissements: listeSurveillee}),
        });
        const json = await reponse.json();

        if (reponse.ok) {
            afficherMsg(msgEtab, "success", "Liste sauvegardée.");
        } else {
            afficherMsg(msgEtab, "danger", json.erreur || "Erreur lors de la sauvegarde.");
        }
    } catch {
        afficherMsg(msgEtab, "danger", "Impossible de contacter le serveur.");
    }
});

function afficherMsg(el, type, texte) {
    el.className = `alert alert-${type} mb-2`;
    el.textContent = texte;
}
