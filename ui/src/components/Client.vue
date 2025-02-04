<template>
    <audio ref="audio" src="/silence.mp3" playsinline autoplay></audio>
    <dialog ref="dialog" class="permission" @cancel.prevent>
        <div class="dialog-header">
            <b>Codex</b>
            <p>
                Hello dear user! We know this is kinda annoying, but we need
                your autoplay permission, so that we can talk to you.
            </p>
        </div>
        <div class="dialog-footer">
            <button class="btn" @click="give_permission">
                Give permission
            </button>
        </div>
    </dialog>
</template>

<style scoped>
audio {
    visibility: hidden;
}

.permission {
    display: none;
    flex-direction: column;
    padding: 0;
    margin: auto;
    outline: none;
    border: 1px solid var(--text-muted);
    border-radius: 0.5rem;
    box-sizing: border-box;
}

.permission[open] {
    display: flex;
}

.permission button {
    margin-left: auto;
}

.dialog-header {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    background-color: var(--foreground-color);
}

.dialog-footer {
    padding: 1rem;
    border-top: 1px solid var(--border-color);
    background-color: var(--background-color);
}
</style>

<script setup>
import { ref, onMounted, onBeforeMount } from "vue";
import { store } from "/src/assets/store.js";

import { RTVIClient } from "@pipecat-ai/client-js";
import { DailyTransport } from "@pipecat-ai/daily-transport";

const audio = ref(null);
const dialog = ref(null);
const rtviClient = ref(null);

async function give_permission() {
    audio.value.play();
    dialog.value.close();
}

function handleBotAudio(track, participant) {
    if (participant.local || track.kind !== "audio") return;
    audio.value.srcObject = new MediaStream([track]);
    audio.value.play();
}

async function setup() {
    console.log("Setting up the client...");
    const transport = new DailyTransport();
    const rtviClient = new RTVIClient({
        transport,
        params: {
            baseUrl: "http://localhost:8000/pipecat",
        },
        enableMic: true,
        enableCam: false,
        callbacks: {
            onTrackStart: handleBotAudio,
        },
    });
    await rtviClient.connect();
}

onMounted(() => {
    audio.value
        .play()
        .then(() => {
            console.log("Autoplay is enabled!");
            setup();
        })
        .catch(() => {
            dialog.value.showModal();
        });
});
</script>
