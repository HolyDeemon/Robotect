<script setup>
import { computed, ref } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import CompareTable from '../components/cabinet/CompareTable.vue'
import SimulationBoard from '../components/cabinet/SimulationBoard.vue'
import SiteFooter from '../components/SiteFooter.vue'
import { calculateObject, serverObjectName } from '../api/server'
import EconomyFigures from '../components/EconomyFigures.vue'
import {
  demoParams,
  getType,
  matchProducts,
  objectTypes,
  parseCsv,
  templateCsv,
  validateParams,
} from '../data/selection'
import { useAuthStore } from '../stores/auth'
import { useProjectStore } from '../stores/projects'

const auth = useAuthStore()
const projectStore = useProjectStore()
const tab = ref('projects')
const screen = ref('list')
const workTab = ref('compare')
const activeId = ref(null)
const typeId = ref('warehouse')
const params = ref(demoParams('warehouse'))
const errors = ref([])
const result = ref(null)
const economy = ref(null)
const economyState = ref('')
const economyError = ref('')
const economyProgress = ref({ done: 0, total: 14, label: '' })
const compared = ref([])
const forced = ref([])
const enterpriseType = ref('warehouse')
const fileMessage = ref('')
const fileOk = ref(true)
const fileInput = ref(null)

const email = computed(() => auth.user?.email || '')
const economyReady = computed(() => (
  economyState.value !== 'loading' && Boolean(economy.value) && !economyError.value
))
const owned = computed(() => projectStore.forUser(email.value))
const visible = computed(() => (
  tab.value === 'favorites' ? owned.value.filter((item) => item.favorite) : owned.value
))
const active = computed(() => projectStore.find(activeId.value))
const enterprise = computed(() => projectStore.enterpriseOf(email.value))
const current = computed(() => getType(typeId.value))
const groups = computed(() => [...new Set(current.value.fields.map((item) => item.group))])
const comparedItems = computed(() => {
  if (!result.value) return []
  const byId = new Map()
  result.value.matched.forEach((item) => byId.set(item.product.id, item))
  result.value.excluded.forEach((item) => {
    byId.set(item.product.id, { product: item.product, score: null, reasons: item.reasons })
  })
  return compared.value.map((id) => byId.get(id)).filter(Boolean)
})

function showTab(name) {
  tab.value = name
  screen.value = 'list'
}

function load(project) {
  activeId.value = project.id
  typeId.value = project.typeId
  params.value = { ...project.params }
  compared.value = [...(project.compared || [])]
  forced.value = [...(project.forced || [])]
  errors.value = []
  economy.value = null
  economyError.value = ''
  economyState.value = ''
  economyProgress.value = { done: 0, total: 14, label: '' }
  result.value = project.calculated ? matchProducts(project.typeId, project.params) : null
}

function openSimulation() {
  if (!economyReady.value) return
  workTab.value = 'sim'
}

async function refreshEconomy() {
  if (workTab.value === 'sim') workTab.value = 'compare'
  economyState.value = 'loading'
  economyError.value = ''
  economyProgress.value = { done: 0, total: 14, label: 'Записываем параметры объекта' }
  try {
    const saved = await calculateObject(current.value, params.value, (progress) => {
      economyProgress.value = progress
      economy.value = progress.economy
    })
    economy.value = saved.economy
    economyError.value = saved.error
  } catch (error) {
    economy.value = null
    const text = error?.message || 'Не удалось записать параметры.'
    economyError.value = text.length < 180 ? text : 'Параметры не записались, экономика не посчитана.'
  } finally {
    economyState.value = ''
  }
}

function persist() {
  if (!activeId.value) return
  projectStore.update(activeId.value, {
    typeId: typeId.value,
    params: { ...params.value },
    compared: [...compared.value],
    forced: [...forced.value],
    calculated: Boolean(result.value),
    draft: !result.value,
  })
}

function createProject() {
  const saved = enterprise.value
  const project = projectStore.create(email.value, saved?.typeId || 'warehouse', saved?.params)
  load(project)
  tab.value = 'projects'
  screen.value = 'edit'
}

function openProject(project) {
  load(project)
  tab.value = 'projects'
  workTab.value = 'compare'
  screen.value = 'work'
  if (project.calculated) refreshEconomy()
}

function choose(id) {
  typeId.value = id
  params.value = demoParams(id)
  errors.value = []
  result.value = null
}

function fieldsIn(group) {
  return current.value.fields.filter((item) => item.group === group)
}

function errorFor(key) {
  return errors.value.find((item) => item.key === key)?.message || ''
}

function optionLabel(field, value) {
  return field.options.find((item) => item.id === value)?.label || value
}

async function runSelection() {
  errors.value = validateParams(typeId.value, params.value)
  if (errors.value.length) return
  result.value = matchProducts(typeId.value, params.value)
  compared.value = []
  forced.value = []
  persist()
  workTab.value = 'compare'
  screen.value = 'work'
  await refreshEconomy()
}

function saveAndExit() {
  persist()
  screen.value = 'list'
}

function toggleFavorite(project) {
  projectStore.update(project.id, { favorite: !project.favorite })
}

function removeProject(project) {
  if (!project) return
  if (!window.confirm(`Удалить «${project.name}»? Это нельзя отменить.`)) return
  projectStore.remove(project.id)
  if (activeId.value === project.id) {
    activeId.value = null
    result.value = null
    screen.value = 'list'
  }
}

function toggleCompare(id) {
  compared.value = compared.value.includes(id)
    ? compared.value.filter((item) => item !== id)
    : [...compared.value, id]
  persist()
}

function forceAdd(id) {
  if (!forced.value.includes(id)) forced.value = [...forced.value, id]
  if (!compared.value.includes(id)) compared.value = [...compared.value, id]
  persist()
}

function downloadTemplate() {
  const blob = new Blob([templateCsv(enterpriseType.value)], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `robotect-${enterpriseType.value}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

function onEnterpriseFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    const parsed = parseCsv(String(reader.result), enterpriseType.value)
    tab.value = 'enterprise'
    screen.value = 'list'
    if (parsed.error) {
      fileOk.value = false
      fileMessage.value = parsed.error
      return
    }
    projectStore.setEnterprise(email.value, {
      typeId: enterpriseType.value,
      params: { ...demoParams(enterpriseType.value), ...parsed.params },
      fileName: file.name,
    })
    fileOk.value = true
    fileMessage.value = 'Данные предприятия загружены.'
  }
  reader.readAsText(file, 'utf-8')
}

const enterpriseLines = computed(() => {
  const saved = enterprise.value
  if (!saved) return []
  const type = getType(saved.typeId)
  return type.fields.map((field) => ({
    label: field.label,
    value: field.type === 'select'
      ? field.options.find((option) => option.id === saved.params[field.key])?.label || saved.params[field.key]
      : saved.params[field.key],
    unit: field.unit,
  }))
})
</script>

<template>
  <div class="page">
    <AppHeader />
    <section class="board">
      <nav class="tabs" aria-label="Разделы кабинета">
        <button type="button" :class="{ active: tab === 'projects' && screen === 'list' }" @click="showTab('projects')">☆ Проекты</button>
        <button type="button" :class="{ active: tab === 'enterprise' && screen === 'list' }" @click="showTab('enterprise')">☆ Данные предприятия</button>
        <button type="button" :class="{ active: tab === 'favorites' && screen === 'list' }" @click="showTab('favorites')">☆ Избранное</button>
      </nav>
      <input ref="fileInput" class="hidden" type="file" accept=".csv,text/csv" @change="onEnterpriseFile" />

      <div v-if="screen === 'list' && tab !== 'enterprise'">
        <h1>Главная</h1>
        <div class="actions">
          <button type="button" @click="createProject">Создать проект</button>
          <button type="button" @click="fileInput?.click()">Загрузить данные предприятия</button>
        </div>
        <p v-if="!visible.length" class="note">
          {{ tab === 'favorites' ? 'В избранном пока пусто. Отметьте проект звездой.' : 'Проектов пока нет.' }}
        </p>
        <article v-for="project in visible" :key="project.id" class="project">
          <button type="button" class="star" :aria-label="project.favorite ? 'Убрать из избранного' : 'В избранное'" @click="toggleFavorite(project)">
            {{ project.favorite ? '★' : '☆' }}
          </button>
          <button type="button" class="open" @click="openProject(project)">{{ project.name }}</button>
          <span v-if="project.draft" class="draft">Черновик</span>
          <button type="button" class="remove" @click="removeProject(project)">Удалить</button>
        </article>
      </div>

      <div v-else-if="screen === 'list'">
        <h1>Данные предприятия</h1>
        <div class="actions">
          <label>
            Тип объекта
            <select v-model="enterpriseType">
              <option v-for="type in objectTypes" :key="type.id" :value="type.id">{{ type.title }}</option>
            </select>
          </label>
          <button type="button" @click="downloadTemplate">Шаблон CSV</button>
          <button type="button" @click="fileInput?.click()">Загрузить CSV</button>
        </div>
        <p v-if="fileMessage" class="note" :class="{ bad: !fileOk }">{{ fileMessage }}</p>
        <p v-if="!enterprise" class="note">Загрузите CSV с параметрами объекта. Новый проект можно создать уже с этими данными.</p>
        <ul v-else class="facts">
          <li v-for="line in enterpriseLines" :key="line.label">
            <span>{{ line.label }}</span>
            <b>{{ line.value }}<template v-if="line.unit"> {{ line.unit }}</template></b>
          </li>
        </ul>
      </div>

      <div v-else-if="screen === 'work' && active">
        <h1>{{ active.name }}</h1>
        <div class="work-actions">
          <button type="button" class="mint" @click="screen = 'edit'">Изменить</button>
          <button type="button" class="ghost" @click="saveAndExit">Сохранить и выйти</button>
          <button type="button" class="remove" @click="removeProject(active)">Удалить</button>
        </div>
        <div class="subtabs">
          <button type="button" :class="{ active: workTab === 'compare' }" @click="workTab = 'compare'">Таблица сравнений</button>
          <button type="button" :class="{ active: workTab === 'sim' }" :disabled="!economyReady" @click="openSimulation">Симуляция</button>
        </div>
        <p v-if="economyState === 'loading'" class="note">Симуляция откроется, когда экономика будет посчитана.</p>
        <p v-else-if="economyError" class="note bad">Симуляция закрыта, пока экономика не посчитается.</p>
        <div v-if="workTab === 'compare'">
          <p v-if="!result" class="note">Сначала нажмите «Изменить» и подберите решения.</p>
          <template v-else>
            <EconomyFigures
              v-if="economyState === 'loading' || economy"
              :economy="economy"
              :loading="economyState === 'loading'"
              :progress="economyProgress"
              :error="economyError"
            />
            <article v-for="item in result.matched" :key="item.product.id" class="hit">
              <div>
                <h3>{{ item.product.name }}</h3>
                <p>{{ item.product.company }}</p>
              </div>
              <label class="check">
                <input type="checkbox" :checked="compared.includes(item.product.id)" @change="toggleCompare(item.product.id)" />
                В сравнение
              </label>
            </article>
            <article v-for="item in result.excluded" :key="item.product.id" class="hit muted">
              <div>
                <h3>{{ item.product.name }}</h3>
                <p>{{ item.reasons.join('. ') }}</p>
              </div>
              <button type="button" @click="forceAdd(item.product.id)">Всё равно сравнить</button>
            </article>
            <p v-if="!comparedItems.length" class="note">Отметьте решения для таблицы.</p>
            <CompareTable v-else :items="comparedItems" :forced="forced" :staff-cost="params.staffCost" :economy="economy" />
          </template>
        </div>
        <SimulationBoard
          v-else-if="economyReady"
          :user-id="email || auth.user?.id"
          :object-type="serverObjectName[typeId] || 'Склад'"
          :robot-count="Math.max(compared.length, 1)"
          :economy="economy"
        />
      </div>

      <div v-else>
        <h1>{{ active?.name || 'Новый проект' }}</h1>
        <div v-if="active" class="work-actions">
          <button type="button" class="remove" @click="removeProject(active)">Удалить проект</button>
        </div>
        <div class="types">
          <button v-for="type in objectTypes" :key="type.id" type="button" :class="{ active: type.id === typeId }" @click="choose(type.id)">
            {{ type.title }}
          </button>
        </div>
        <label class="field">
          <span>Процесс</span>
          <select v-model="params.process">
            <option v-for="process in current.processes" :key="process.id" :value="process.id">{{ process.label }}</option>
          </select>
          <em v-if="errorFor('process')">{{ errorFor('process') }}</em>
        </label>
        <section v-for="group in groups" :key="group" class="group">
          <h2>{{ group }}</h2>
          <div class="fields">
            <label v-for="item in fieldsIn(group)" :key="item.key" class="field">
              <span>{{ item.label }} <b v-if="item.unit">{{ item.unit }}</b></span>
              <select v-if="item.type === 'select'" v-model="params[item.key]">
                <option v-for="option in item.options" :key="option.id" :value="option.id">{{ option.label }}</option>
              </select>
              <input v-else v-model="params[item.key]" type="number" :min="item.min" :max="item.max" :placeholder="String(item.demo)" />
              <small>По умолчанию: {{ item.type === 'select' ? optionLabel(item, item.demo) : item.demo }}</small>
              <em v-if="errorFor(item.key)">{{ errorFor(item.key) }}</em>
            </label>
          </div>
        </section>
        <button type="button" class="submit" @click="runSelection">Подобрать решения</button>
      </div>
    </section>
    <SiteFooter />
  </div>
</template>

<style scoped>
.page {
  width: min(1200px, calc(100% - 40px));
  margin: 20px auto 0;
}

.board {
  margin-top: 10px;
  padding: 32px;
  background: #fff;
  border-radius: 35px;
}

.hidden {
  display: none;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 28px;
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 16px;
}

.tabs button,
.types button,
.actions button,
.work-actions button,
.hit button,
.submit {
  border: 0;
  background: transparent;
  color: var(--text);
  cursor: pointer;
}

.tabs button {
  height: 40px;
  border-radius: 12px;
  font-size: 16px;
}

.tabs button.active {
  background: #eef0ff;
}

h1 {
  margin: 0 0 16px;
  font-size: 32px;
  font-weight: 700;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 18px;
  margin-bottom: 16px;
  padding: 14px 18px;
  background: #eef0ff;
}

.actions button,
.work-actions button,
.hit button,
.submit {
  height: 40px;
  padding: 0 16px;
  border: 1px solid #cfcfe8;
  border-radius: 10px;
  background: #fff;
}

.actions label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  color: var(--muted);
}

.actions select,
.field input,
.field select {
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  color: var(--text);
}

.note,
.field small,
.facts span,
.hit p {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.45;
}

.note.bad,
.field em {
  color: #9b2c2c;
  font-style: normal;
}

.project {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 8px 16px;
  border: 1px solid var(--line);
  border-radius: 16px;
}

.star,
.open {
  border: 0;
  background: transparent;
  cursor: pointer;
  color: var(--text);
}

.open {
  flex: 1;
  padding: 10px 0;
  font-size: 16px;
  text-align: left;
}

.draft {
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  color: var(--muted);
  font-size: 14px;
}

.remove,
.work-actions .remove {
  border: 0;
  background: transparent;
  color: #9b2c2c;
  cursor: pointer;
  font-size: 14px;
}

.facts {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.facts li {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

.work-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
}

.mint {
  background: #bdf2de;
  border-color: #baddd0;
}

.subtabs {
  display: flex;
  gap: 18px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--line);
}

.subtabs button {
  padding: 8px 2px 10px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  cursor: pointer;
}

.subtabs button:disabled {
  color: var(--muted);
  cursor: default;
}

.subtabs button.active {
  border-bottom-color: var(--text);
}

.types {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.types button {
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 12px;
}

.types button.active {
  background: #b6b9fe;
  border-color: #b6b9fe;
}

.fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.group h2,
.hit h3 {
  margin: 16px 0 8px;
  font-size: 18px;
}

.field b {
  color: var(--muted);
  font-weight: 400;
}

.submit {
  margin-top: 20px;
  background: #2c2c2c;
  color: #f5f5f5;
  border: 0;
}

.hit {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 12px;
}

.hit h3,
.hit p {
  margin: 0;
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

@media (max-width: 900px) {
  .board {
    padding: 16px;
    border-radius: 24px;
  }

  .tabs,
  .fields {
    grid-template-columns: 1fr;
  }
}
</style>
