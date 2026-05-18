"use strict";

const etablissements = [];

document.getElementById("btn-ajouter-etab").addEventListener("click", () => {
    const saisie = document.getElementById("ins-etab-saisie");
    const nom = saisie.value.trim();
    if (!nom || etablissements.includes(nom)) {
        saisie.value = "";
        return;
    }
    etablissements.push(nom);
    saisie.value = "";
    afficherListeEtab();
});

function afficherListeEtab() {
    const liste = document.getElementById("liste-etab");
    liste.innerHTML = "";
    etablissements.forEach((nom, index) => {
        const li = document.createElement("li");
        li.className = "list-group-item d-flex justify-content-between align-items-center";
        li.textContent = nom;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-sm btn-outline-danger";
        btn.textContent = "Retirer";
        btn.addEventListener("click", () => {
            etablissements.splice(index, 1);
            afficherListeEtab();
        });
        li.appendChild(btn);
        liste.appendChild(li);
    });
}

document.getElementById("form-inscription").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const msgSucces = document.getElementById("msg-succes");
    const msgErreur = document.getElementById("msg-erreur");

    msgSucces.classList.add("d-none");
    msgErreur.classList.add("d-none");

    if (!form.checkValidity()) {
        form.classList.add("was-validated");
        return;
    }

    const donnees = {
        nom_complet: document.getElementById("ins-nom").value.trim(),
        courriel: document.getElementById("ins-courriel").value.trim(),
        mot_de_passe: document.getElementById("ins-mdp").value,
        etablissements_surveilles: [...etablissements],
    };

    try {
        const reponse = await fetch("/api/utilisateurs", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(donnees),
        });
        const json = await reponse.json();

        if (reponse.ok) {
            msgSucces.textContent = "Profil créé avec succès ! Vous pouvez maintenant vous connecter.";
            msgSucces.classList.remove("d-none");
            form.reset();
            form.classList.remove("was-validated");
            etablissements.length = 0;
            afficherListeEtab();
        } else {
            msgErreur.textContent = json.erreur || "Une erreur est survenue.";
            msgErreur.classList.remove("d-none");
        }
    } catch {
        msgErreur.textContent = "Impossible de contacter le serveur.";
        msgErreur.classList.remove("d-none");
    }
});
