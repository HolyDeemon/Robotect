<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  text: {
    type: String,
    required: true,
  },
  to: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <component :is="to ? 'RouterLink' : 'article'" class="card" :to="to || undefined">
    <h2>{{ title }}</h2>
    <p>{{ text }}</p>
  </component>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 24px;
  min-width: 0;
  padding: 24px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: inherit;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    border-color 0.25s ease;
}

a.card:hover {
  transform: translateY(-6px);
  border-color: #b6b9fe;
  box-shadow: 0 14px 32px rgba(99, 102, 255, 0.14);
}

a.card:focus-visible {
  outline: 2px solid #6366ff;
  outline-offset: 3px;
}

@media (prefers-reduced-motion: reduce) {
  .card {
    transition: none;
  }

  a.card:hover {
    transform: none;
  }
}

h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

p {
  margin: 0;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--muted);
}
</style>
