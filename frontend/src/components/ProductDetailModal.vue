<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  compared: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'compare'])
const router = useRouter()

const caseOpen = ref(true)
const specsOpen = ref(true)
const liked = ref(false)

watch(
  () => props.product.id,
  () => {
    caseOpen.value = true
    specsOpen.value = true
    liked.value = false
  },
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})

function onKeydown(event) {
  if (event.key === 'Escape') emit('close')
}

function goPick() {
  emit('close')
  router.push({ path: '/pick', query: { product: props.product.id } })
}
</script>

<template>
  <div class="backdrop" @click.self="emit('close')">
    <article class="dialog" role="dialog" aria-modal="true" :aria-label="product.name">
      <button type="button" class="close" aria-label="Закрыть" @click="emit('close')">×</button>

      <div class="layout">
        <div class="media">
          <div class="picture" aria-hidden="true">
            <svg viewBox="0 0 48 48">
              <rect x="6" y="10" width="36" height="28" rx="3" fill="none" stroke="currentColor" stroke-width="2" />
              <circle cx="16" cy="20" r="3" fill="currentColor" />
              <path d="M8 34 L18 24 L26 31 L32 25 L40 34" fill="none" stroke="currentColor" stroke-width="2" />
            </svg>
          </div>

          <section class="fold">
            <button type="button" class="fold-head" @click="caseOpen = !caseOpen">
              <span>Кейс</span>
              <svg viewBox="0 0 16 16" :class="{ up: caseOpen }" aria-hidden="true">
                <path d="M3 6 L8 11 L13 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              </svg>
            </button>
            <p v-if="caseOpen">{{ product.caseText }}</p>
          </section>
        </div>

        <div class="info">
          <div class="pick-row">
            <button type="button" class="pick" @click="goPick">Подобрать решение</button>
          </div>

          <div class="title-row">
            <div class="title">
              <h2>{{ product.name }}</h2>
              <span class="status">{{ product.status }}</span>
            </div>
            <button
              type="button"
              class="heart"
              :class="{ on: liked }"
              :aria-pressed="liked"
              aria-label="В избранное"
              @click="liked = !liked"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M12 20s-7-4.4-7-9.2A3.8 3.8 0 0 1 12 8a3.8 3.8 0 0 1 7 2.8C19 15.6 12 20 12 20z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.6"
                />
              </svg>
            </button>
          </div>
          <p class="company">{{ product.company }}</p>
          <p class="price">{{ product.price.toLocaleString('ru-RU') }} тыс.руб</p>
          <p>{{ product.solutionType }}</p>
          <p class="muted">{{ product.subtype }}</p>
          <p class="scenario">{{ product.scenario }}</p>

          <section class="fold specs">
            <button type="button" class="fold-head" @click="specsOpen = !specsOpen">
              <span>ТТХ</span>
              <svg viewBox="0 0 16 16" :class="{ up: specsOpen }" aria-hidden="true">
                <path d="M3 6 L8 11 L13 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              </svg>
            </button>
            <ul v-if="specsOpen">
              <li v-for="line in product.specs" :key="line">{{ line }}</li>
            </ul>
          </section>

          <button type="button" class="compare" @click="emit('compare')">
            {{ compared ? 'Выбрано для сравнения' : 'Выбрать решение для сравнения' }}
          </button>
        </div>
      </div>
    </article>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(30, 30, 30, 0.35);
}

.dialog {
  position: relative;
  width: min(920px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  padding: 28px;
  background: #fff;
  border-radius: 24px;
}

.close {
  position: absolute;
  top: 12px;
  right: 16px;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--text);
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 28px;
  align-items: start;
}

.media,
.info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.picture {
  display: grid;
  place-items: center;
  width: 100%;
  aspect-ratio: 1.15;
  background: #e8e8e8;
  color: #d0d0d0;
}

.picture svg {
  width: 120px;
  height: 120px;
}

.fold {
  border: 1px solid var(--line);
  border-radius: 8px;
}

.fold-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px 14px;
  border: 0;
  background: transparent;
  color: var(--text);
  font-size: 16px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}

.fold-head svg {
  width: 16px;
  height: 16px;
}

.fold-head svg.up {
  transform: rotate(180deg);
}

.fold p,
.fold ul {
  margin: 0;
  padding: 0 14px 14px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.45;
}

.fold ul {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 14px;
  list-style: none;
}

.pick-row {
  display: flex;
  justify-content: flex-end;
  min-height: 40px;
  padding-right: 36px;
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.pick {
  height: 40px;
  padding: 0 16px;
  border: 1px solid #baddd0;
  border-radius: 8px;
  background: #bdf2de;
  color: #2c2c2c;
  font-weight: 600;
  cursor: pointer;
}

.heart {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 50%;
  background: #2c2c2c;
  color: #fff;
  cursor: pointer;
}

.heart svg {
  width: 22px;
  height: 22px;
}

.heart.on svg path {
  fill: #fff;
}

.title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

h2,
p {
  margin: 0;
}

h2 {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.status {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 8px;
  background: #d8f8ea;
  font-size: 14px;
}

.company {
  font-size: 20px;
}

.price {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.muted,
.scenario {
  color: var(--muted);
}

.scenario {
  font-style: italic;
}

.specs .fold-head {
  font-size: 16px;
}

.compare {
  height: 44px;
  border: 0;
  border-radius: 8px;
  background: #2c2c2c;
  color: #f5f5f5;
  font-weight: 600;
  cursor: pointer;
}

@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .pick-row {
    padding-right: 28px;
  }

  h2 {
    font-size: 26px;
  }
}
</style>
