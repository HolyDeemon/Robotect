<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  mode: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['close', 'switch'])

const auth = useAuthStore()
const error = ref('')
const form = ref(emptyForm())

const isLogin = computed(() => props.mode === 'login')
const title = computed(() => (isLogin.value ? 'Войти' : 'Зарегистрироваться'))

watch(
  () => props.mode,
  () => {
    error.value = ''
    form.value = emptyForm()
  },
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})

function emptyForm() {
  return {
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    passwordCheck: '',
  }
}

function onKeydown(event) {
  if (event.key === 'Escape') emit('close')
}

function submit() {
  error.value = ''
  try {
    if (isLogin.value) {
      auth.login({ email: form.value.email, password: form.value.password })
    } else {
      auth.register(form.value)
    }
    emit('close')
  } catch (reason) {
    error.value = reason.message
  }
}
</script>

<template>
  <div class="backdrop" @click.self="emit('close')">
    <form class="dialog" @submit.prevent="submit">
      <div class="dialog-head">
        <h2>{{ title }}</h2>
        <button type="button" class="close" aria-label="Закрыть" @click="emit('close')">×</button>
      </div>

      <label v-if="!isLogin">
        Имя
        <input v-model="form.firstName" type="text" autocomplete="given-name" required />
      </label>
      <label v-if="!isLogin">
        Фамилия
        <input v-model="form.lastName" type="text" autocomplete="family-name" required />
      </label>
      <label>
        Электронная почта
        <input v-model="form.email" type="email" autocomplete="email" required />
      </label>
      <label>
        Пароль
        <input v-model="form.password" type="password" autocomplete="current-password" minlength="5" required />
      </label>
      <label v-if="!isLogin">
        Повторите пароль
        <input v-model="form.passwordCheck" type="password" autocomplete="new-password" minlength="5" required />
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <button class="submit" type="submit">{{ title }}</button>

      <button
        v-if="isLogin"
        type="button"
        class="switch"
        @click="emit('switch', 'register')"
      >
        Нет аккаунта? Зарегистрироваться
      </button>
      <button v-else type="button" class="switch" @click="emit('switch', 'login')">
        Уже есть аккаунт? Войти
      </button>
    </form>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(30, 30, 30, 0.35);
}

.dialog {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: min(420px, 100%);
  margin: 0;
  padding: 28px;
  background: #fff;
  border-radius: 24px;
}

.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.close {
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

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  color: var(--muted);
}

input {
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  outline: none;
  background: #fff;
  color: var(--text);
}

input:focus {
  border-color: #767676;
}

.error {
  margin: 0;
  color: #9b2c2c;
  font-size: 14px;
}

.submit {
  height: 40px;
  border: 1px solid #2c2c2c;
  border-radius: 8px;
  background: #2c2c2c;
  color: #f5f5f5;
  cursor: pointer;
}

.switch {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text);
  font-size: 14px;
  text-align: center;
  cursor: pointer;
}
</style>
