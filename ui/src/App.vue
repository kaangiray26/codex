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
            <span class="placeholder" :loaded="store.document_loaded">
                <github_alt />
                <i>Upload a file to get started</i>
            </span>
            <div class="transcript-container">
                <p>{{ store.transcripts[0] }}</p>
            </div>
        </div>
        <div class="chat-input" :disabled="!store.connected">
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
                :disabled="!store.connected"
            />
        </div>
    </main>
    <Client ref="client" @transcript="handle_transcript" />
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { store } from "/src/assets/store.js";
import Client from "./components/Client.vue";

import cloud from "./icons/cloud.vue";
import github_alt from "./icons/github-alt.vue";

const client = ref(null);

function browse_files() {
    document.querySelector("#file").click();
}

async function upload_file(event) {
    const file = event.target.files[0];

    // Construct a FormData object
    // so that we can send the file to the server
    const formData = new FormData();
    formData.append("file", file);

    // Send the file to the server
    const response = await codex.upload(formData);
    if (!response) {
        alert("Document could not be uploaded. Please try again.");
        return;
    }

    // Update the store with the response
    store.document = response.data.document;
    await nextTick();
    store.document_loaded = true;

    // Connect to the server
    await client.value.connect();
}

function handle_transcript(text) {
    store.transcripts.push(text);
}

onMounted(() => {
    setInterval(() => {
        if (store.transcripts.length > 0) {
            store.transcripts.shift();
        }
    }, 3000);
});
</script>
