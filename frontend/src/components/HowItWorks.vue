<script setup>
const steps = [
  {
    title: 'Шаг 1',
    text: 'Выберите отрасль и задайте параметры для подбора решений',
  },
  {
    title: 'Шаг 2',
    text: 'Платформа подберёт и сравнит применимые решения',
  },
  {
    title: 'Шаг 3',
    text: 'Платформа произведет экономические расчеты и вы увидете экономический эффект',
  },
  {
    title: 'Шаг 4',
    text: 'Сравните основные предложенные сценарии',
  },
  {
    title: 'Шаг 5',
    text: 'Построение симуляции работы робота на 2D-схеме объекта и изменение показателей эффективности',
  },
  {
    title: 'Шаг 6',
    text: 'Сохраните проект в вашем личном кабинете и вы всегда сможете вернуться к нему',
  },
]
</script>

<template>
  <section class="how" aria-labelledby="how-title">
    <h2 id="how-title">Как работает платформа</h2>
    <ol class="timeline">
      <li v-for="(step, index) in steps" :key="step.title" class="step">
        <div class="node" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</div>
        <h3>{{ step.title }}</h3>
        <p>{{ step.text }}</p>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.how {
  padding: 72px 0 120px;
}

h2 {
  margin: 0 0 48px;
  font-size: 40px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.03em;
  text-align: center;
}

.timeline {
  position: relative;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  margin: 0;
  padding: 0;
  list-style: none;
}

.timeline::before {
  content: '';
  position: absolute;
  top: 21px;
  left: calc(100% / 12);
  right: calc(100% / 12);
  height: 2px;
  background: #1e1e1e;
}

.step {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 10px;
  text-align: center;
}

.node {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  margin-bottom: 16px;
  border: 1.5px solid #1e1e1e;
  border-radius: 50%;
  background: var(--bg);
  font-size: 14px;
  font-weight: 700;
}

h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

p {
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
  color: var(--muted);
}

@media (max-width: 900px) {
  h2 {
    margin-bottom: 32px;
    font-size: 28px;
  }

  .timeline {
    display: flex;
    gap: 0;
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .timeline::before {
    left: 90px;
    right: auto;
    width: 900px;
  }

  .step {
    flex: 0 0 180px;
  }
}
</style>
