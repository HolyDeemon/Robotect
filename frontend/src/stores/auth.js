import { ref } from 'vue'
import { defineStore } from 'pinia'

const SESSION_KEY = 'robotect-session'

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function messageFrom(data) {
  const detail = typeof data.detail === 'string' ? data.detail : ''
  const text = detail.toLowerCase()

  if (text.includes('неверный email') || text.includes('не найден') || text.includes('401')) {
    return 'Неверный email или пароль'
  }
  if (text.includes('duplicate') || text.includes('unique') || text.includes('уже')) {
    return 'Такой email уже зарегистрирован. Войдите в аккаунт.'
  }
  if (Array.isArray(data.detail) && data.detail.length) {
    return 'Проверьте поля: пароль от 5 символов, имя от 3 до 50.'
  }
  if (text.includes('connection') || text.includes('connect')) {
    return 'База сейчас недоступна. Попробуйте ещё раз чуть позже.'
  }
  return 'Не удалось выполнить запрос. Попробуйте ещё раз.'
}

async function request(path, body) {
  let response
  try {
    response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error('Сервер входа не отвечает. Запустите базу и сервис входа.')
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(messageFrom(data))
  return data
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref(readJson(SESSION_KEY, null))
  const notice = ref('')
  let noticeTimer

  function showNotice(text) {
    notice.value = text
    clearTimeout(noticeTimer)
    noticeTimer = setTimeout(() => {
      notice.value = ''
    }, 4000)
  }

  async function register({ firstName, lastName, email, password, passwordCheck }) {
    const name = `${firstName.trim()} ${lastName.trim()}`.trim()
    const mail = email.trim()

    if (name.length < 3 || name.length > 50) {
      throw new Error('Имя и фамилия вместе должны быть от 3 до 50 символов')
    }
    if (password.length < 5) {
      throw new Error('Пароль должен быть от 5 символов')
    }
    if (password !== passwordCheck) {
      throw new Error('Пароли не совпадают')
    }

    await request('/api/users/register', { email: mail, password, name })
    saveSession({ name, email: mail })
  }

  async function login({ email, password }) {
    const mail = email.trim()
    const data = await request('/api/users/login', { email: mail, password })
    saveSession({ name: data.name || mail, email: mail, id: data.user_id })
  }

  function logout() {
    user.value = null
    notice.value = ''
    localStorage.removeItem(SESSION_KEY)
  }

  function saveSession(session) {
    user.value = session
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  }

  return { user, notice, showNotice, register, login, logout }
})
