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
        <ChatToolbar ref="chat_toolbar" @connect="handle_connect" />
    </main>
    <Client ref="client" @transcript="handle_transcript" />
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { store } from "/src/assets/store.js";
import Client from "./components/Client.vue";
import ChatToolbar from "./components/ChatToolbar.vue";

import github_alt from "./icons/github-alt.vue";

const client = ref(null);

function handle_transcript(text) {
    store.transcripts.push(text);
}

async function handle_connect() {
    await client.value.connect();
}

onMounted(() => {
    setInterval(() => {
        if (store.transcripts.length > 0) {
            store.transcripts.shift();
        }
    }, 3000);
});
</script>
