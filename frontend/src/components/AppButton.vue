<script setup>
defineProps({
  variant: {
    type: String,
    default: 'ghost',
  },
  size: {
    type: String,
    default: 'sm',
  },
  href: {
    type: String,
    default: '#',
  },
})
</script>

<template>
  <a class="btn" :class="[variant, size]" :href="href">
    <slot />
  </a>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 16px;
  line-height: 1;
  white-space: nowrap;
}

.sm {
  padding: 8px;
}

.md {
  padding: 12px;
}

.ghost {
  background: #e3e3e3;
  border: 1px solid #767676;
  color: #1e1e1e;
}

.dark {
  background: #2c2c2c;
  border: 1px solid #2c2c2c;
  color: #f5f5f5;
}
</style>
