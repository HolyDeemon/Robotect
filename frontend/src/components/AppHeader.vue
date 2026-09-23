<script setup>
import { nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppButton from './AppButton.vue'
import AuthModal from './AuthModal.vue'

const auth = useAuthStore()
const router = useRouter()
const modal = ref(null)

const links = [
  { label: 'Каталог', to: '/catalog' },
  { label: 'Подобрать решение', to: '/pick' },
  { label: 'Связь с нами', href: '#' },
]

const open = ref(false)
const query = ref('')
const field = ref(null)

async function toggleSearch() {
  open.value = !open.value
  if (open.value) {
    await nextTick()
    field.value?.focus()
  }
}

function closeSearch() {
  if (!query.value) open.value = false
}

function submitSearch() {
  const text = query.value.trim()
  if (!text) return
  router.push({ path: '/catalog', query: { q: text } })
  open.value = false
}
</script>

<template>
  <header class="header">
    <a class="logo-link" href="/" aria-label="Robotect">
      <img class="logo" src="/logo_Robotect.png" alt="" />
    </a>

    <nav class="nav" aria-label="Основное меню">
      <template v-for="link in links" :key="link.label">
        <RouterLink v-if="link.to" :to="link.to" active-class="is-active">{{ link.label }}</RouterLink>
        <a v-else :href="link.href">{{ link.label }}</a>
      </template>
    </nav>

    <form class="search" :class="{ open }" role="search" @submit.prevent="submitSearch">
      <input
        ref="field"
        v-model="query"
        class="search-field"
        type="search"
        aria-label="Поиск по сайту"
        :tabindex="open ? 0 : -1"
        @blur="closeSearch"
      />
      <button
        type="button"
        class="search-toggle"
        aria-label="Поиск по сайту"
        :aria-expanded="open"
        @mousedown.prevent
        @click="toggleSearch"
      >
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.6" />
          <path d="M10.5 10.5 L14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        </svg>
      </button>
    </form>

    <div v-if="auth.user" class="auth">
      <span class="user-name">{{ auth.user.firstName }} {{ auth.user.lastName }}</span>
      <button type="button" class="logout" aria-label="Выйти" @click="auth.logout()">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M10 7V5a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-2" fill="none" stroke="currentColor" stroke-width="1.6" />
          <path d="M13 12H4m0 0 3-3m-3 3 3 3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>
    <div v-else class="auth">
      <AppButton href="#" @click.prevent="modal = 'login'">Войти</AppButton>
      <AppButton variant="dark" href="#" @click.prevent="modal = 'register'">Зарегистрироваться</AppButton>
    </div>

    <AuthModal v-if="modal" :mode="modal" @close="modal = null" @switch="modal = $event" />
  </header>
</template>

<style scoped>
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 24px;
  padding: 32px;
  background: var(--surface);
  border-radius: 35px;
}

.logo {
  display: block;
  width: 40px;
  height: 43px;
  object-fit: contain;
}

.nav {
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.nav a {
  padding: 8px;
  border-radius: 8px;
  font-size: 16px;
  line-height: 1;
}

.nav a.is-active {
  background: #b6b9fe;
}

.search {
  position: relative;
  flex: none;
  width: 40px;
  height: 40px;
}

.search-field {
  position: absolute;
  top: 0;
  right: 48px;
  width: 0;
  height: 40px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 9999px;
  outline: none;
  background: #fff;
  color: var(--text);
  opacity: 0;
  pointer-events: none;
  transition: width 0.2s ease, opacity 0.2s ease, padding 0.2s ease;
}

.search.open .search-field {
  width: 200px;
  padding: 0 16px;
  border-color: var(--line);
  opacity: 1;
  pointer-events: auto;
}

.search-toggle {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 9999px;
  background: #fff;
  color: var(--text);
  cursor: pointer;
}

.search-toggle svg {
  width: 16px;
  height: 16px;
}

.auth {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
}

.logout {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 9999px;
  background: #fff;
  color: var(--text);
  cursor: pointer;
}

.logout svg {
  width: 18px;
  height: 18px;
}

@media (max-width: 900px) {
  .header {
    padding: 20px;
    border-radius: 24px;
  }

  .auth {
    margin-left: auto;
  }

  .nav {
    order: 4;
    flex-basis: 100%;
  }
}
</style>
