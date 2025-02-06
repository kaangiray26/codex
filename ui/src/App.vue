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
            <Transcripts ref="transcripts" />
            <Citations ref="citations" />
        </div>
        <ChatToolbar ref="chat_toolbar" @connect="handle_connect" />
    </main>
    <Client
        ref="client"
        @transcript="handle_transcript"
        @started="handle_started"
        @clear_transcripts="transcripts.clear"
    />
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { store } from "/src/assets/store.js";
import Client from "./components/Client.vue";
import ChatToolbar from "./components/ChatToolbar.vue";
import Transcripts from "./components/Transcripts.vue";
import Citations from "./components/Citations.vue";

import github_alt from "./icons/github-alt.vue";

const client = ref(null);
const transcripts = ref([]);

async function handle_connect() {
    await client.value.connect();
}

function handle_transcript(text) {
    console.log("Adding:", text);
    transcripts.value.add_transcript(text);
}

function handle_started() {
    transcripts.value.process_queue();
}

onMounted(() => {
    // Periodically check the transcripts
});
</script>
