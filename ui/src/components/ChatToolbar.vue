<template>
    <div class="chat-input">
        <div
            v-if="!store.document_loaded"
            class="input-container"
            :disabled="!store.connected"
        >
            <label for="file">
                <cloud_arrow_up />
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
        <div v-else class="input-container">
            <label>
                <book />
                <span>{{ store.document.filename }}</span>
            </label>
            <button class="btn" @click="toggle_citations">Citations</button>
        </div>
    </div>
</template>

<script setup>
import { ref } from "vue";
import { store } from "/src/assets/store.js";
import book from "/src/icons/book.vue";
import cloud_arrow_up from "/src/icons/cloud-arrow-up.vue";

const emit = defineEmits(["connect"]);

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
    store.document_loaded = true;

    // Connect to the server
    emit("connect");
}

function toggle_citations() {
    store.show_citations = !store.show_citations;
}
</script>
