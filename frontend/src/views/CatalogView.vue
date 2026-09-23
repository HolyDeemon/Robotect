<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import CatalogFilters from '../components/CatalogFilters.vue'
import ProductCard from '../components/ProductCard.vue'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import SiteFooter from '../components/SiteFooter.vue'
import { emptyFilters, products } from '../data/catalog'

const route = useRoute()
const filters = ref(emptyFilters())
const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const sort = ref('new')
const page = ref(1)
const pageSize = 4

watch(
  () => route.query.q,
  (value) => {
    query.value = typeof value === 'string' ? value : ''
    page.value = 1
  },
)
const opened = ref(null)
const compared = ref([])

const filtered = computed(() => {
  const text = query.value.trim().toLowerCase()
  return products
    .filter((item) => {
      if (text && !`${item.name} ${item.company} ${item.purpose}`.toLowerCase().includes(text)) return false
      if (!matchesList(item, 'company')) return false
      if (!matchesList(item, 'solutionType')) return false
      if (!matchesList(item, 'purpose')) return false
      if (!matchesList(item, 'country')) return false
      if (!matchesList(item, 'status')) return false
      if (!matchesList(item, 'navigation')) return false
      if (!matchesList(item, 'acquisition')) return false
      if (filters.value.objects.length && !item.objects.some((value) => filters.value.objects.includes(value))) return false
      if (filters.value.infra.length && !filters.value.infra.every((value) => item.infra.includes(value))) return false
      if (filters.value.hasCases && !item.hasCases) return false
      if (filters.value.confirmed && !item.confirmed) return false
      if (item.payload > filters.value.payload) return false
      if (item.autonomy > filters.value.autonomy) return false
      if (item.price > filters.value.price) return false
      if (item.serviceLife > filters.value.serviceLife) return false
      return true
    })
    .sort(compare)
})

const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const visible = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))

watch(filtered, () => {
  if (page.value > pages.value) page.value = pages.value
})

function matchesList(item, key) {
  const selected = filters.value[key]
  return !selected.length || selected.includes(item[key])
}

function compare(a, b) {
  if (sort.value === 'price-asc') return a.price - b.price
  if (sort.value === 'price-desc') return b.price - a.price
  return b.created.localeCompare(a.created)
}

function toggleCompare(product) {
  compared.value = compared.value.includes(product.id)
    ? compared.value.filter((id) => id !== product.id)
    : [...compared.value, product.id]
}
</script>

<template>
  <div class="page">
    <AppHeader />
    <section class="board">
      <CatalogFilters v-model="filters" />
      <div class="results">
        <div class="toolbar">
          <label class="search">
            <input v-model="query" type="search" placeholder="Поиск" aria-label="Поиск по каталогу" />
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.6" />
              <path d="M10.5 10.5 L14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
          </label>
          <RouterLink class="pick" to="/pick">Подобрать решение</RouterLink>
          <div class="sort">
            <button type="button" :class="{ active: sort === 'new' }" @click="sort = 'new'">Сначала новые</button>
            <button type="button" :class="{ active: sort === 'price-asc' }" @click="sort = 'price-asc'">Цена ↑</button>
            <button type="button" :class="{ active: sort === 'price-desc' }" @click="sort = 'price-desc'">Цена ↓</button>
          </div>
        </div>

        <div v-if="visible.length" class="grid">
          <ProductCard
            v-for="product in visible"
            :key="product.id"
            :product="product"
            @open="opened = product"
          />
        </div>
        <p v-else class="empty">По выбранным фильтрам решений нет.</p>

        <nav class="pager" aria-label="Страницы каталога">
          <button type="button" :disabled="page === 1" @click="page -= 1">← Previous</button>
          <button
            v-for="number in pages"
            :key="number"
            type="button"
            :class="{ current: number === page }"
            @click="page = number"
          >
            {{ number }}
          </button>
          <button type="button" :disabled="page === pages" @click="page += 1">Next →</button>
        </nav>
      </div>
    </section>
    <SiteFooter />
    <ProductDetailModal
      v-if="opened"
      :product="opened"
      :compared="compared.includes(opened.id)"
      @close="opened = null"
      @compare="toggleCompare(opened)"
    />
  </div>
</template>

<style scoped>
.page {
  width: min(1200px, calc(100% - 40px));
  margin: 20px auto 0;
}

.board {
  display: flex;
  align-items: flex-start;
  gap: 32px;
  margin-top: 10px;
  padding: 32px;
  background: #fff;
  border-radius: 35px;
}

.results {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 32px;
  min-width: 0;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 160px;
  height: 40px;
  padding: 0 16px;
  border: 1px solid var(--line);
  border-radius: 9999px;
}

.search input {
  width: 100%;
  min-width: 0;
  padding: 0;
  border: 0;
  outline: none;
}

.search svg {
  width: 16px;
  height: 16px;
}

.pick {
  display: inline-flex;
  align-items: center;
  height: 46px;
  padding: 0 16px;
  border: 1px solid #baddd0;
  border-radius: 8px;
  background: #bdf2de;
  color: #2c2c2c;
  font-weight: 600;
  cursor: pointer;
}

.sort {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.sort button,
.pager button {
  height: 36px;
  padding: 0 12px;
  border: 0;
  border-radius: 8px;
  background: #f5f5f5;
  color: var(--muted);
  cursor: pointer;
}

.sort button.active,
.pager button.current {
  background: #2c2c2c;
  color: #f5f5f5;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.empty {
  margin: 0;
  color: var(--muted);
}

.pager {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.pager button:disabled {
  opacity: 0.5;
  cursor: default;
}

@media (max-width: 900px) {
  .board {
    flex-direction: column;
    padding: 16px;
    border-radius: 24px;
  }

  .grid {
    grid-template-columns: 1fr;
  }

  .sort {
    margin-left: 0;
  }
}
</style>
