<template>
    <header>
        <span>Codex</span>
        <label
            :connected="store.connected"
            :title="
                store.connected
                    ? ''
                    : 'Could not connect to the server, please refresh the page.'
            "
        ></label>
    </header>
    <main>
        <div class="chat-display">
            <span class="placeholder">
                <github_alt />
                Upload a file to get started
            </span>
        </div>
        <div class="chat-input">
            <label for="file">
                <cloud />
                <span>Upload</span>
            </label>
            <button class="btn" @click="browse_files">Browse files</button>
            <input
                type="file"
                id="file"
                accept="application/pdf"
                @change="upload_file"
            />
        </div>
    </main>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { store } from "/src/assets/store.js";

import cloud from "./icons/cloud.vue";
import github_alt from "./icons/github-alt.vue";

function browse_files() {
    document.querySelector("#file").click();
}

async function upload_file(event) {
    console.log(event.target.files[0]);
    const file = event.target.files[0];

    // Send the file to the server
}
</script>
