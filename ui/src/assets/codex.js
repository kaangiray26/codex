import { store } from "./store.js";

const ADDRESS = "http://localhost:8000";

class Codex {
    constructor() {
        // Try to connect to the backend
        this.connect();
    }

    // No need for an async function here,
    // as we are not waiting for a response.
    // I'm looking at you, 'frontend developers'...
    connect() {
        fetch(ADDRESS)
            .then((res) => {
                if (res.ok) {
                    store.connected = true;
                    return;
                }
                store.connected = false;
            })
            .catch((err) => {
                store.connected = false;
                console.error(err);
            });
    }

    async upload(formData) {
        const address = `${ADDRESS}/upload`;
        return await fetch(address, {
            method: "POST",
            body: formData,
        })
            .then((res) => res.json())
            .catch((err) => {
                console.error(err);
                return null;
            });
    }
}

// Attach the codex object to the window
document.addEventListener("DOMContentLoaded", () => {
    window.codex = new Codex();
    console.log("Codex ready!");
});
