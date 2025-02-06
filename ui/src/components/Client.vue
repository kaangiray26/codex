<template>
    <audio ref="audio" src="silence.mp3" playsinline autoplay></audio>
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

import { RTVIClient, RTVIEvent } from "@pipecat-ai/client-js";
import { DailyTransport } from "@pipecat-ai/daily-transport";
import AudioMotionAnalyzer from "audiomotion-analyzer";

const emit = defineEmits(["transcript", "started"]);

const audio = ref(null);
const audioMotion = ref(null);

const dialog = ref(null);
const rtviClient = new RTVIClient({
    params: {
        baseUrl: "http://localhost:8000",
    },
    transport: new DailyTransport(),
    enableMic: true,
    enableCam: false,
    callbacks: {
        onConnected: () => {
            console.log("Connected to the server!");
        },
        onDisconnected: () => {
            console.log("Disconnected from the server!");
        },
        onBotConnected: () => {
            console.log("Bot connected!");
        },
        onBotDisconnected: () => {
            console.log("Bot disconnected!");
        },
        onGenericMessage: (data) => {
            console.log("Generic message:", data);
            if (!data.hasOwnProperty("sources")) return;
            store.sources = data.sources;
            store.show_citations = true;
        },
        // Handle transport state changes
        onTransportStateChanged: (state) => {
            if (state === "ready") setupMediaTracks();
        },
    },
});

async function give_permission() {
    audio.value.play();
    dialog.value.close();
}

function setupEventListeners() {
    // Listen for new tracks starting
    rtviClient.on(RTVIEvent.TrackStarted, (track, participant) => {
        console.info("Participant:", participant);
        if (participant?.local) return;
        setupAudioTrack(track);
    });

    // Transcripts
    rtviClient.on(RTVIEvent.UserTranscript, (data) => {
        console.log("User:", data.text);
    });

    rtviClient.on(RTVIEvent.BotTranscript, (data) => {
        console.log("Bot:", data.text);
        emit("transcript", data.text);
    });

    rtviClient.on(RTVIEvent.BotLlmText, (data) => {
        console.log("Bot LLM:", data.text);
    });

    rtviClient.on(RTVIEvent.BotStartedSpeaking, (track, participant) => {
        store.bot_speaking = true;
        emit("started");
        console.info("Bot speaking...");
    });

    rtviClient.on(RTVIEvent.BotStoppedSpeaking, (track, participant) => {
        store.bot_speaking = false;
        console.info("Bot stopped speaking...");
    });
}

function setupAudioTrack(track) {
    // Check if we're already playing this track
    if (audio.value.srcObject) {
        const oldTrack = audio.value.srcObject.getAudioTracks()[0];
        if (oldTrack?.id === track.id) return;
    }
    // Create a new MediaStream with the track and set it as the audio source
    audio.value.srcObject = new MediaStream([track]);
}

function setupMediaTracks() {
    console.log("Setting up media tracks...");
    // Get current tracks from the client
    const tracks = rtviClient.tracks();
    console.log("Tracks:", tracks);
    if (!tracks.bot?.audio) return;

    console.log("Setting up audio track");
    const track = tracks.bot.audio;

    // Check if we're already playing this track
    if (audio.value.srcObject) {
        const oldTrack = audio.value.srcObject.getAudioTracks()[0];
        if (oldTrack?.id === track.id) return;
    }
    // Create a new MediaStream with the track and set it as the audio source
    audio.value.srcObject = new MediaStream([track]);
}

async function setup() {
    // Set listeners
    setupEventListeners();

    // Init media devices
    await rtviClient.initDevices();
}

async function connect() {
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

    // Initialize AudioMotion for visualizer
    const container = document.querySelector(".chat-display");
    audioMotion.value = new AudioMotionAnalyzer(container, {
        ansiBands: false,
        showScaleX: false,
        bgAlpha: 0,
        overlay: true,
        mode: 1,
        frequencyScale: "log",
        radial: true,
        roundBars: true,
        radius: 0,
        mirror: true,
        radialInvert: true,
        showPeaks: false,
        gradient: "prism",
        channelLayout: "dual-vertical",
        smoothing: 0.5,
        source: audio.value,
        connectSpeakers: false,
    });
});

defineExpose({
    connect,
});
</script>
