import { ref } from 'vue'
import { defineStore } from 'pinia'

const USERS_KEY = 'robotect-users'
const SESSION_KEY = 'robotect-session'

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref(readJson(SESSION_KEY, null))

  function register({ firstName, lastName, email, password, passwordCheck }) {
    const name = firstName.trim()
    const surname = lastName.trim()
    const mail = email.trim()

    if (name.length < 2 || surname.length < 2) {
      throw new Error('Введите имя и фамилию')
    }
    if (password.length < 5) {
      throw new Error('Пароль должен быть от 5 символов')
    }
    if (password !== passwordCheck) {
      throw new Error('Пароли не совпадают')
    }

    const users = readJson(USERS_KEY, [])
    if (users.some((item) => item.email === mail)) {
      throw new Error('Пользователь с такой почтой уже зарегистрирован')
    }

    users.push({ firstName: name, lastName: surname, email: mail, password })
    localStorage.setItem(USERS_KEY, JSON.stringify(users))
    saveSession({ firstName: name, lastName: surname, email: mail })
  }

  function login({ email, password }) {
    const mail = email.trim()
    const found = readJson(USERS_KEY, []).find((item) => item.email === mail && item.password === password)
    if (!found) {
      throw new Error('Неверная почта или пароль')
    }
    saveSession({ firstName: found.firstName, lastName: found.lastName, email: found.email })
  }

  function logout() {
    user.value = null
    localStorage.removeItem(SESSION_KEY)
  }

  function saveSession(session) {
    user.value = session
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  }

  return { user, register, login, logout }
})
