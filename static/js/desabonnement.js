"use strict";

document.getElementById("btn-confirmer").addEventListener("click", async () => {
    const msgErreur = document.getElementById("msg-erreur");
    msgErreur.classList.add("d-none");

    try {
        const reponse = await fetch("/api/desabonnement", {
            method: "DELETE",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({token: TOKEN_DESABONNEMENT}),
        });
        const json = await reponse.json();

        if (reponse.ok) {
            document.getElementById("vue-confirmation").classList.add("d-none");
            document.getElementById("vue-succes").classList.remove("d-none");
        } else {
            msgErreur.textContent = json.erreur || "Une erreur est survenue.";
            msgErreur.classList.remove("d-none");
        }
    } catch {
        msgErreur.textContent = "Impossible de contacter le serveur.";
        msgErreur.classList.remove("d-none");
    }
});
