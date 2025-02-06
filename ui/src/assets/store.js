// store.js
import { reactive } from "vue";

export const store = reactive({
    connected: false,
    document_loaded: false,
    document: null,
    bot_speaking: false,
    transcripts: [],
});
