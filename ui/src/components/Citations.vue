<template>
    <Transition>
        <div class="citations-container" v-if="store.show_citations">
            <b>Citations</b>
            <ul>
                <li v-for="source in store.extra.sources">
                    {{ source }}
                </li>
            </ul>
        </div>
    </Transition>
</template>

<style scoped>
.citations-container {
    position: absolute;
    top: 1rem;
    right: 1rem;
    gap: 0.5rem;
    display: flex;
    flex-direction: column;
    background-color: var(--background-color);
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    box-sizing: border-box;
    max-width: calc(50% - 1rem);
    max-height: calc(100% - 2rem);
    overflow: auto;
    z-index: 100;
}

.citations-container ul {
    margin: 0;
    padding: 0;
    list-style-type: none;
}

@media (max-width: 1200px) {
    .citations-container {
        max-width: calc(100% - 2rem);
    }
}
</style>

<script setup>
import { ref } from "vue";
import { store } from "/src/assets/store.js";
</script>
