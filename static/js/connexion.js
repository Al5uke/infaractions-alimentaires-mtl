"use strict";

document.getElementById("form-connexion").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const msgErreur = document.getElementById("msg-erreur");
    msgErreur.classList.add("d-none");

    if (!form.checkValidity()) {
        form.classList.add("was-validated");
        return;
    }

    const donnees = {
        courriel: document.getElementById("cx-courriel").value.trim(),
        mot_de_passe: document.getElementById("cx-mdp").value,
    };

    try {
        const reponse = await fetch("/api/connexion", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(donnees),
        });
        const json = await reponse.json();

        if (reponse.ok) {
            window.location.href = "/profil";
        } else {
            msgErreur.textContent = json.erreur || "Identifiants incorrects.";
            msgErreur.classList.remove("d-none");
        }
    } catch {
        msgErreur.textContent = "Impossible de contacter le serveur.";
        msgErreur.classList.remove("d-none");
    }
});
