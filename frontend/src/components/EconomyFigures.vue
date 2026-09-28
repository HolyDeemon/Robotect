<script setup>
import { computed } from 'vue'
import { formatMetric } from '../api/server'

const props = defineProps({
  economy: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  progress: { type: Object, default: () => ({ done: 0, total: 14, label: '' }) },
  error: { type: String, default: '' },
})

const rows = [
  { key: 'robots', label: 'Число роботов', unit: 'шт.' },
  { key: 'capex', label: 'CAPEX', unit: 'руб.' },
  { key: 'opex', label: 'OPEX за год', unit: 'руб.' },
  { key: 'effect', label: 'Годовой эффект', unit: 'руб.' },
  { key: 'payback', label: 'Окупаемость', unit: 'лет' },
  { key: 'roi', label: 'ROI', unit: '%' },
  { key: 'tco', label: 'TCO', unit: 'руб.' },
]

const percent = computed(() => {
  const total = props.progress?.total || 1
  return Math.min(100, Math.round(((props.progress?.done || 0) / total) * 100))
})

function cell(scenario, key) {
  const value = props.economy?.[scenario]?.[key]
  if (value === null) return '—'
  if (value === undefined) return props.loading ? '…' : '—'
  return formatMetric(value)
}
</script>

<template>
  <section class="figures" :class="{ loading }">
    <header>
      <h2>Экономика объекта</h2>
      <p>Одни и те же параметры считаются в двух сценариях. Колонки — это сценарии, строки — показатели.</p>
    </header>

    <div v-if="loading" class="progress" role="progressbar" :aria-valuenow="percent" aria-valuemin="0" aria-valuemax="100">
      <div class="track"><span :style="{ width: `${percent}%` }"></span></div>
      <small>{{ progress.label || 'Считаем…' }} · {{ percent }}%</small>
    </div>
    <p v-else-if="error" class="error">{{ error }}</p>

    <table>
      <thead>
        <tr>
          <th>Показатель</th>
          <th class="opt">Оптимистичный</th>
          <th class="pess">Пессимистичный</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.key">
          <th>{{ row.label }}</th>
          <td class="opt">{{ cell('opt', row.key) }} <small>{{ row.unit }}</small></td>
          <td class="pess">{{ cell('pess', row.key) }} <small>{{ row.unit }}</small></td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.figures {
  margin: 0 0 28px;
  padding: 22px;
  border: 2px solid #6366ff;
  border-radius: 24px;
  background: #eef0ff;
}

header h2 {
  margin: 0 0 6px;
  font-size: 28px;
}

header p,
.progress small,
.error {
  margin: 0;
  color: #1e1e1e;
  font-size: 14px;
  line-height: 1.45;
}

.progress {
  margin: 16px 0;
}

.track {
  height: 12px;
  overflow: hidden;
  border-radius: 999px;
  background: #fff;
}

.track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #6366ff;
  transition: width 0.25s ease;
}

.progress small,
.error {
  display: block;
  margin-top: 8px;
}

.error {
  color: #9b2c2c;
}

table {
  width: 100%;
  margin-top: 16px;
  border-collapse: collapse;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
}

th,
td {
  padding: 12px 14px;
  border-bottom: 1px solid #d9d9d9;
  text-align: left;
}

thead th {
  font-size: 14px;
}

tbody th {
  font-weight: 600;
}

td small {
  color: #757575;
  font-size: 13px;
}

.opt {
  background: #bdf2de;
}

.pess {
  background: #f3e4ff;
}

thead .opt,
thead .pess {
  font-weight: 700;
}
</style>
