<template>
    <div class="transcript-container">
        <p>{{ transcript }}</p>
    </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
const queue = ref([]);
const transcript = ref("");
const is_processing = ref(false);

function add_transcript(text) {
    // Calculate duration
    const duration = Math.ceil(text.split(" ").length / 3) * 1000;
    queue.value.push({ text, duration });
}

async function process_queue() {
    // Check if we're already processing a transcript
    if (is_processing.value || !queue.value.length) return;

    // Set processing flag
    is_processing.value = true;

    // Process the next transcript
    const { text, duration } = queue.value.shift();
    transcript.value = text;

    // Wait until the transcript is rendered
    await nextTick();

    // Wait for the duration
    await new Promise((resolve) => setTimeout(resolve, duration));
    transcript.value = "";
    is_processing.value = false;
    process_queue();
}

defineExpose({
    add_transcript,
    process_queue,
});
</script>
