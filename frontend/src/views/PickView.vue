<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import SiteFooter from '../components/SiteFooter.vue'
import { products } from '../data/catalog'
import {
  compareRows,
  demoParams,
  getType,
  matchProducts,
  objectTypes,
  parseCsv,
  templateCsv,
  validateParams,
} from '../data/selection'

const route = useRoute()
const typeId = ref('warehouse')
const params = ref(demoParams('warehouse'))
const errors = ref([])
const fileMessage = ref('')
const fileOk = ref(false)
const result = ref(null)
const compared = ref([])
const forced = ref([])
const resultsEl = ref(null)
const fileInput = ref(null)

const current = computed(() => getType(typeId.value))
const groups = computed(() => [...new Set(current.value.fields.map((item) => item.group))])
const focusProduct = computed(() => products.find((item) => item.id === Number(route.query.product)) || null)

watch(
  () => route.query.object,
  (value) => {
    if (objectTypes.some((item) => item.id === value)) choose(value)
  },
  { immediate: true },
)

const comparedItems = computed(() => {
  if (!result.value) return []
  const byId = new Map()
  result.value.matched.forEach((item) => byId.set(item.product.id, item))
  result.value.excluded.forEach((item) => {
    byId.set(item.product.id, { product: item.product, score: null, forced: true, reasons: item.reasons })
  })
  return compared.value.map((id) => byId.get(id)).filter(Boolean)
})

function choose(id) {
  typeId.value = id
  params.value = demoParams(id)
  errors.value = []
  fileMessage.value = ''
  result.value = null
  compared.value = []
  forced.value = []
}

function fieldsIn(group) {
  return current.value.fields.filter((item) => item.group === group)
}

function errorFor(key) {
  return errors.value.find((item) => item.key === key)?.message || ''
}

function applyDemo() {
  params.value = demoParams(typeId.value)
  errors.value = []
  fileMessage.value = 'Подставлен демонстрационный набор. Его можно изменить.'
  fileOk.value = true
}

function downloadTemplate() {
  const blob = new Blob([templateCsv(typeId.value)], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `robotect-${typeId.value}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

function onFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv')) {
    fileOk.value = false
    fileMessage.value = 'Сейчас принимается CSV. В Excel сохраните таблицу как CSV и загрузите снова.'
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    const parsed = parseCsv(String(reader.result), typeId.value)
    if (parsed.error) {
      fileOk.value = false
      fileMessage.value = parsed.error
      return
    }
    params.value = { ...demoParams(typeId.value), ...parsed.params }
    errors.value = validateParams(typeId.value, params.value)
    fileOk.value = errors.value.length === 0
    fileMessage.value = errors.value.length
      ? 'Файл прочитан, но часть полей вне допустимого диапазона. Исправьте отмеченные поля.'
      : 'Параметры загружены из CSV.'
  }
  reader.readAsText(file, 'utf-8')
}

async function run() {
  errors.value = validateParams(typeId.value, params.value)
  fileMessage.value = ''
  if (errors.value.length) {
    result.value = null
    return
  }
  result.value = matchProducts(typeId.value, params.value)
  const focusId = focusProduct.value?.id
  const focusMatched = result.value.matched.some((item) => item.product.id === focusId)
  compared.value = focusMatched ? [focusId] : []
  forced.value = []
  await nextTick()
  resultsEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function toggleCompare(id) {
  compared.value = compared.value.includes(id)
    ? compared.value.filter((item) => item !== id)
    : [...compared.value, id]
}

function forceAdd(id) {
  if (!forced.value.includes(id)) forced.value = [...forced.value, id]
  if (!compared.value.includes(id)) compared.value = [...compared.value, id]
}

function optionLabel(field, value) {
  return field.options.find((item) => item.id === value)?.label || value
}
</script>

<template>
  <div class="page">
    <AppHeader />
    <section class="board">
      <header class="intro">
        <p class="steps">1. Объект · 2. Параметры · 3. Подборка</p>
        <h1>Подобрать решение</h1>
        <p class="lead">
          Платформа смотрит на тип объекта, процесс и ограничения и объясняет, почему решение
          подходит или не подходит. Это предварительная оценка, не обследование объекта.
        </p>
      </header>

      <div class="types" role="listbox" aria-label="Тип объекта">
        <button
          v-for="type in objectTypes"
          :key="type.id"
          type="button"
          role="option"
          :aria-selected="type.id === typeId"
          :class="{ active: type.id === typeId }"
          @click="choose(type.id)"
        >
          <strong>{{ type.title }}</strong>
          <span>{{ type.lead }}</span>
        </button>
      </div>

      <p v-if="focusProduct" class="from-card">
        Вы перешли из карточки «{{ focusProduct.name }}». Если оно не попадёт в подборку, его всё равно
        можно добавить в сравнение — с предупреждением.
      </p>

      <div class="form-head">
        <h2>Параметры: {{ current.title }}</h2>
        <div class="tools">
          <button type="button" @click="applyDemo">Демонстрационные данные</button>
          <button type="button" @click="downloadTemplate">Шаблон CSV</button>
          <label class="upload">
            Загрузить CSV
            <input ref="fileInput" type="file" accept=".csv,text/csv" @change="onFile" />
          </label>
        </div>
      </div>
      <p v-if="fileMessage" class="note" :class="{ bad: !fileOk }">{{ fileMessage }}</p>
      <p v-if="errors.length" class="note bad">Заполните обязательные поля и проверьте диапазоны. Подсказка под полем говорит, что исправить.</p>

      <label class="field">
        <span>Процесс <i>*</i></span>
        <select v-model="params.process">
          <option v-for="process in current.processes" :key="process.id" :value="process.id">
            {{ process.label }}
          </option>
        </select>
        <small>От процесса зависит, какие назначения попадут в подборку.</small>
        <em v-if="errorFor('process')">{{ errorFor('process') }}</em>
      </label>

      <section v-for="group in groups" :key="group" class="group">
        <h3>{{ group }}</h3>
        <div class="fields">
          <label v-for="item in fieldsIn(group)" :key="item.key" class="field">
            <span>
              {{ item.label }}
              <i v-if="item.required">*</i>
              <b v-if="item.unit">{{ item.unit }}</b>
            </span>
            <select v-if="item.type === 'select'" v-model="params[item.key]">
              <option v-for="option in item.options" :key="option.id" :value="option.id">{{ option.label }}</option>
            </select>
            <input
              v-else
              v-model="params[item.key]"
              type="number"
              :min="item.min"
              :max="item.max"
              :step="item.min < 1 ? '0.1' : '1'"
              :placeholder="String(item.demo)"
            />
            <small>
              {{ item.hint }}
              <template v-if="item.hint"> · </template>
              По умолчанию: {{ item.type === 'select' ? optionLabel(item, item.demo) : item.demo }}{{ item.unit ? ` ${item.unit}` : '' }}.
              Источник: {{ item.source }}.
            </small>
            <em v-if="errorFor(item.key)">{{ errorFor(item.key) }}</em>
          </label>
        </div>
      </section>

      <button type="button" class="submit" @click="run">Подобрать решения</button>

      <div v-if="result" ref="resultsEl" class="results">
        <h2>Подборка</h2>
        <p class="lead">
          Оценка от 0 до 100 складывается из шести критериев: запас грузоподъёмности, автономность,
          кейсы, подтвержденность данных, доступность и инфраструктура. Жёсткое ограничение исключает
          решение: другой объект, другой процесс, недостаточная грузоподъёмность, снятие с поставки
          или неподходящая среда.
        </p>
        <p class="count">
          Подходит {{ result.matched.length }} из {{ result.matched.length + result.excluded.length }}.
          Исключено {{ result.excluded.length }}.
        </p>

        <article v-for="item in result.matched" :key="item.product.id" class="hit">
          <div class="hit-top">
            <div>
              <h3>{{ item.product.name }}</h3>
              <p>{{ item.product.company }} · {{ item.product.purpose }}</p>
            </div>
            <div class="score">
              <strong>{{ item.score }}</strong>
              <span>из 100</span>
            </div>
          </div>
          <span class="badge" :class="{ warn: item.needsCheck }">
            {{ item.needsCheck ? 'Требует проверки' : 'Подходит' }}
          </span>
          <ul class="reasons">
            <li v-for="reason in item.reasons" :key="reason">{{ reason }}</li>
          </ul>
          <ul v-if="item.limits.length" class="limits">
            <li v-for="limit in item.limits" :key="limit">{{ limit }}</li>
          </ul>
          <ul v-if="item.missing.length" class="limits">
            <li v-for="line in item.missing" :key="line">Не хватает данных: {{ line }}</li>
          </ul>
          <div class="factors">
            <p v-for="factor in item.factors" :key="factor.id">
              <span>{{ factor.label }}</span>
              <b>{{ factor.points === null ? 'нет данных' : `${factor.points} из ${factor.weight}` }}</b>
            </p>
          </div>
          <label class="check">
            <input
              type="checkbox"
              :checked="compared.includes(item.product.id)"
              @change="toggleCompare(item.product.id)"
            />
            В сравнение
          </label>
        </article>

        <p v-if="!result.matched.length" class="note">
          По этим параметрам автоматическая подборка пустая. Причины — в списке исключений. Решение
          можно добавить в сравнение вручную.
        </p>

        <h2>Не вошли в подборку</h2>
        <article v-for="item in result.excluded" :key="item.product.id" class="miss">
          <div>
            <h3>{{ item.product.name }}</h3>
            <p>{{ item.product.company }}</p>
            <ul>
              <li v-for="reason in item.reasons" :key="reason">{{ reason }}</li>
            </ul>
          </div>
          <button type="button" @click="forceAdd(item.product.id)">Всё равно сравнить</button>
        </article>

        <h2>Сравнение</h2>
        <p v-if="!comparedItems.length" class="note">Отметьте решения в подборке или добавьте исключённое вручную.</p>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Характеристика</th>
                <th v-for="item in comparedItems" :key="item.product.id">
                  {{ item.product.name }}
                  <small v-if="forced.includes(item.product.id)">Добавлено вручную</small>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in compareRows" :key="row.label">
                <th>{{ row.label }}</th>
                <td v-for="item in comparedItems" :key="item.product.id">{{ row.value(item) }}</td>
              </tr>
              <tr v-if="forced.length">
                <th>Предупреждение</th>
                <td v-for="item in comparedItems" :key="item.product.id">
                  <template v-if="forced.includes(item.product.id)">
                    Не прошло отбор: {{ item.reasons.join('. ') }}
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
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

.intro h1,
.form-head h2,
.results h2,
.group h3,
.hit h3,
.miss h3,
p {
  margin: 0;
}

.steps {
  color: var(--muted);
  font-size: 14px;
}

h1 {
  margin: 8px 0;
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.lead,
.note,
small,
.field small {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.45;
}

.types {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin: 24px 0;
}

.types button,
.tools button,
.upload,
.miss button {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fff;
  color: var(--text);
  cursor: pointer;
}

.types button {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 16px;
  text-align: left;
}

.types button.active {
  background: #b6b9fe;
  border-color: #b6b9fe;
}

.types span,
.from-card {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.4;
}

.types button.active span {
  color: var(--text);
}

.from-card,
.note {
  margin-bottom: 16px;
}

.note.bad,
.field em {
  color: #9b2c2c;
  font-style: normal;
}

.form-head,
.hit-top,
.miss {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.tools {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tools button,
.upload,
.miss button {
  height: 40px;
  padding: 0 14px;
  border-radius: 8px;
}

.upload {
  display: inline-flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.upload input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.group {
  margin-top: 24px;
}

.group h3 {
  margin-bottom: 12px;
  font-size: 18px;
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
  margin-top: 16px;
}

.group .field {
  margin-top: 0;
}

.field span {
  font-size: 14px;
}

.field i {
  color: #9b2c2c;
  font-style: normal;
}

.field b {
  color: var(--muted);
  font-weight: 400;
}

.field input,
.field select {
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  color: var(--text);
}

.submit,
.miss button {
  border: 0;
  background: #2c2c2c;
  color: #f5f5f5;
}

.submit {
  height: 46px;
  margin-top: 24px;
  padding: 0 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.results {
  margin-top: 40px;
  scroll-margin-top: 20px;
}

.results h2 {
  margin: 28px 0 8px;
  font-size: 28px;
}

.count {
  margin: 8px 0 16px;
}

.hit,
.miss {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 16px;
}

.hit h3,
.miss h3 {
  font-size: 20px;
}

.score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  color: #6366ff;
}

.score strong {
  font-size: 32px;
  line-height: 1;
}

.badge {
  display: inline-flex;
  width: fit-content;
  margin: 10px 0;
  padding: 4px 10px;
  border-radius: 8px;
  background: #d8f8ea;
  font-size: 14px;
}

.badge.warn {
  background: #fff3c4;
}

.reasons,
.limits {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
  line-height: 1.45;
}

.limits {
  color: var(--muted);
}

.factors {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
  margin: 12px 0;
}

.factors p {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th,
td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}

thead th {
  font-size: 16px;
}

thead small,
td {
  color: var(--muted);
}

thead small {
  display: block;
  font-weight: 400;
}

@media (max-width: 900px) {
  .board {
    padding: 16px;
    border-radius: 24px;
  }

  .types,
  .fields,
  .factors {
    grid-template-columns: 1fr;
  }

  h1 {
    font-size: 32px;
  }

  .form-head,
  .miss,
  .hit-top {
    flex-direction: column;
  }
}
</style>
