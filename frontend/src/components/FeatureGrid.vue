<script setup>
import FeatureCard from './FeatureCard.vue'

const cards = [
  {
    title: 'Каталог решений',
    text: 'Роботы от разных вендоров с характеристиками, стоимостью и применимостью — в одном месте.',
    to: '/catalog',
  },
  {
    title: 'Подбор под объект',
    text: 'Платформа подберёт применимые решения по параметрам вашего объекта и объяснит, почему они подходят.',
    to: '/pick',
  },
  {
    title: 'Сравнение решений',
    text: 'Сравнение роботов в одной таблице по техническим, эксплуатационным и экономическим характеристикам.',
    to: '/pick',
  },
  {
    title: 'Симуляция работы',
    text: '2D-схема объекта, работа роботов и KPI в реальном времени — вы увидете, как решение окупается.',
  },
  {
    title: 'Отчёт для руководства',
    text: 'Экспортируйте файлы и используйте их в подготовке презентационных материалов.',
  },
]
</script>

<template>
  <section class="grid" aria-label="Возможности платформы">
    <FeatureCard
      v-for="card in cards"
      :key="card.title"
      :title="card.title"
      :text="card.text"
      :to="card.to"
    />
  </section>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 48px;
  padding: 64px 0;
}

.grid > :nth-child(-n + 3) {
  grid-column: span 2;
}

.grid > :nth-child(n + 4) {
  grid-column: span 3;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 32px 0;
  }

  .grid > :nth-child(-n + 3),
  .grid > :nth-child(n + 4) {
    grid-column: auto;
  }
}
</style>
