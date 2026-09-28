import { ref } from 'vue'
import { defineStore } from 'pinia'
import { demoParams } from '../data/selection'

const PROJECTS_KEY = 'robotect-projects'
const ENTERPRISE_KEY = 'robotect-enterprise'

function read(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

export const useProjectStore = defineStore('projects', () => {
  const projects = ref(read(PROJECTS_KEY, []))
  const enterprise = ref(read(ENTERPRISE_KEY, {}))

  function saveProjects() {
    localStorage.setItem(PROJECTS_KEY, JSON.stringify(projects.value))
  }

  function saveEnterprise() {
    localStorage.setItem(ENTERPRISE_KEY, JSON.stringify(enterprise.value))
  }

  function forUser(email) {
    if (!email) return []
    return projects.value
      .filter((item) => item.owner === email)
      .slice()
      .sort((a, b) => b.updatedAt - a.updatedAt)
  }

  function find(id) {
    return projects.value.find((item) => item.id === id) || null
  }

  function create(email, typeId = 'warehouse', params) {
    const owned = forUser(email)
    const project = {
      id: crypto.randomUUID(),
      owner: email,
      name: `Проект ${owned.length + 1}`,
      favorite: false,
      draft: true,
      calculated: false,
      typeId,
      params: { ...(params || demoParams(typeId)) },
      compared: [],
      forced: [],
      updatedAt: Date.now(),
    }
    projects.value = [project, ...projects.value]
    saveProjects()
    return project
  }

  function remove(id) {
    projects.value = projects.value.filter((item) => item.id !== id)
    saveProjects()
  }

  function update(id, patch) {
    projects.value = projects.value.map((item) => (
      item.id === id ? { ...item, ...patch, updatedAt: Date.now() } : item
    ))
    saveProjects()
    return find(id)
  }

  function enterpriseOf(email) {
    if (!email) return null
    return enterprise.value[email] || null
  }

  function setEnterprise(email, payload) {
    if (!email) return
    enterprise.value = {
      ...enterprise.value,
      [email]: { ...payload, updatedAt: Date.now() },
    }
    saveEnterprise()
  }

  return { projects, forUser, find, create, update, remove, enterpriseOf, setEnterprise }
})
