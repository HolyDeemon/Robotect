<script setup>
import { RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
</script>

<template>
  <p v-if="auth.notice" class="notice" role="status">{{ auth.notice }}</p>
  <RouterView />
</template>

<style scoped>
.notice {
  position: fixed;
  top: 20px;
  left: 50%;
  z-index: 40;
  margin: 0;
  padding: 12px 18px;
  border-radius: 12px;
  background: #bdf2de;
  color: #1e1e1e;
  font-size: 15px;
  font-weight: 600;
  transform: translateX(-50%);
}
</style>
