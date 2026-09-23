<script setup>
const columns = [
  {
    title: 'Каталог решений',
    links: [
      { label: 'Для склада', href: '#' },
      { label: 'Для аэропорта', href: '#' },
      { label: 'Для медицинского учреждения', href: '#' },
    ],
  },
  {
    title: 'Подбор решений',
    links: [
      { label: 'Демо-подбор', to: '/pick' },
      { label: 'Полный подбор', to: '/pick' },
    ],
  },
  {
    title: 'Компания',
    links: [
      { label: 'О платформе', href: '#' },
      { label: 'Документы', href: '#' },
      { label: 'Контакты', href: '#' },
    ],
  },
  {
    title: 'Связаться с нами',
    links: [],
  },
]
</script>

<template>
  <footer class="footer">
    <section v-for="column in columns" :key="column.title">
      <h2>{{ column.title }}</h2>
      <ul v-if="column.links.length">
        <li v-for="link in column.links" :key="link.label">
          <RouterLink v-if="link.to" :to="link.to">{{ link.label }}</RouterLink>
          <a v-else :href="link.href">{{ link.label }}</a>
        </li>
      </ul>
    </section>
  </footer>
</template>

<style scoped>
.footer {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 32px 32px 40px;
  margin-top: 10px;
  background: var(--surface);
  border-top: 1px solid var(--line);
  border-radius: 35px;
}

h2 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}

ul {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

a {
  font-size: 16px;
  line-height: 1.4;
}

@media (max-width: 900px) {
  .footer {
    grid-template-columns: 1fr 1fr;
    padding-bottom: 48px;
    border-radius: 24px;
  }
}
</style>
