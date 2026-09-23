<script setup>
import robotUrl from '../assets/images/robot.png'
import AppButton from './AppButton.vue'
</script>

<template>
  <section class="hero">
    <div class="copy">
      <h1>Подбор роботов</h1>
      <p>
        Задайте параметры, а платформа сравнит различные решения и предложит лучшие варианты,
        демонстрируя работу роботов на вашем объекте, а также показывет эффект от их использования.
      </p>
      <div class="actions">
        <AppButton size="md" href="/catalog">Смотреть каталог</AppButton>
        <AppButton variant="dark" size="md" href="/pick">Подобрать решение</AppButton>
      </div>
    </div>
    <img class="robot" :src="robotUrl" alt="" />
  </section>
</template>

<style scoped>
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 460px);
  align-items: center;
  gap: 16px;
  padding: 48px 24px 32px;
}

.copy {
  text-align: center;
}

h1 {
  margin: 0 auto;
  max-width: 571px;
  font-size: 72px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.03em;
}

p {
  margin: 8px auto 0;
  max-width: 635px;
  font-size: 24px;
  font-weight: 400;
  line-height: 1.2;
  color: var(--muted);
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
}

.robot {
  display: block;
  width: 100%;
  height: auto;
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 48px 0 24px;
  }

  h1 {
    font-size: 32px;
  }

  p {
    font-size: 18px;
  }

  .actions {
    flex-wrap: wrap;
  }

  .robot {
    max-width: 360px;
    margin: 0 auto;
  }
}
</style>
