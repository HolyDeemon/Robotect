<script setup>
defineProps({
  product: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['open'])

function bars(value, total) {
  return Array.from({ length: total }, (_, index) => index < value)
}
</script>

<template>
  <article class="card" role="button" tabindex="0" @click="emit('open')" @keydown.enter="emit('open')">
    <span class="status">{{ product.status }}</span>
    <div class="picture" aria-hidden="true">
      <svg viewBox="0 0 48 48">
        <rect x="6" y="10" width="36" height="28" rx="3" fill="none" stroke="currentColor" stroke-width="2" />
        <circle cx="16" cy="20" r="3" fill="currentColor" />
        <path d="M8 34 L18 24 L26 31 L32 25 L40 34" fill="none" stroke="currentColor" stroke-width="2" />
      </svg>
    </div>
    <h3>{{ product.name }}</h3>
    <p>{{ product.subtype }}</p>
    <p class="muted">{{ product.company }}</p>
    <p class="scenario">{{ product.scenario }}</p>
    <p class="case">{{ product.caseText }}</p>
    <p class="price">{{ product.price.toLocaleString('ru-RU') }} тыс. руб</p>
    <hr />
    <div class="meter">
      <span>УГТ</span>
      <div class="bars">
        <i v-for="(filled, index) in bars(product.ugt, 9)" :key="index" :class="{ filled }" />
      </div>
      <b>{{ product.ugt }}/9</b>
    </div>
    <hr />
    <div class="meter">
      <span class="small">Расчеты и потенциал</span>
      <div class="bars short">
        <i v-for="(filled, index) in bars(product.potential, 5)" :key="index" :class="{ filled }" />
      </div>
      <b>{{ product.potential }}/5</b>
    </div>
  </article>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
  padding: 16px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  cursor: pointer;
}

.status {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 16px;
  border-radius: 10px;
  background: #b6b9fe;
  font-size: 16px;
}

.picture {
  display: grid;
  place-items: center;
  width: 100%;
  height: 180px;
  background: #e3e3e3;
  color: #c8c8c8;
}

.picture svg {
  width: 72px;
  height: 72px;
}

h3,
p {
  margin: 0;
}

h3,
.price {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}

p {
  font-size: 16px;
  line-height: 1.4;
}

.muted,
.case {
  color: var(--muted);
}

.scenario {
  font-size: 14px;
  font-style: italic;
}

.case {
  font-size: 12px;
}

hr {
  width: 100%;
  margin: 4px 0;
  border: 0;
  border-top: 1px solid var(--line);
}

.meter {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.meter span {
  font-size: 16px;
  font-weight: 600;
}

.small {
  font-size: 10px;
  font-weight: 400;
}

.bars {
  display: flex;
  gap: 3px;
  margin-left: auto;
}

.bars i {
  width: 18px;
  height: 12px;
  border-radius: 3px;
  background: #e6e6e6;
}

.bars i.filled {
  background: #b6b9fe;
}

.meter b {
  font-size: 14px;
  color: #6366ff;
}
</style>
