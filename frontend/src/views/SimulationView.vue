<script setup>
import { computed } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import SimulationBoard from '../components/cabinet/SimulationBoard.vue'
import SiteFooter from '../components/SiteFooter.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const userId = computed(() => auth.user?.email || auth.user?.id || 'guest')
</script>

<template>
  <div class="page">
    <AppHeader />
    <section class="board">
      <h1>Симуляция</h1>
      <p>Карта и показатели приходят с сервера расчёта, как только соединение открыто.</p>
      <SimulationBoard :user-id="userId" object-type="Склад" :robot-count="4" />
    </section>
    <SiteFooter />
  </div>
</template>

<style scoped>
.page {
  width: min(1200px, calc(100% - 40px));
  margin: 20px auto 0;
}

.board {
  margin-top: 10px;
  padding: 32px;
  background: #fff;
  border-radius: 35px;
}

h1 {
  margin: 0 0 8px;
  font-size: 40px;
  letter-spacing: -0.03em;
}

p {
  margin: 0 0 20px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.45;
}

@media (max-width: 900px) {
  .board {
    padding: 16px;
    border-radius: 24px;
  }

  h1 {
    font-size: 32px;
  }
}
</style>
