<script setup>
import { formatMetric } from '../../api/server'
import { compareRows } from '../../data/selection'

const props = defineProps({
  items: { type: Array, required: true },
  forced: { type: Array, required: true },
  staffCost: { type: [Number, String], default: null },
  economy: { type: Object, default: null },
})

const economyRows = [
  { label: 'Число роботов, оптимистичный сценарий', scenario: 'opt', key: 'robots', unit: 'шт.' },
  { label: 'Число роботов, пессимистичный сценарий', scenario: 'pess', key: 'robots', unit: 'шт.' },
  { label: 'CAPEX, оптимистичный сценарий', scenario: 'opt', key: 'capex', unit: 'руб.' },
  { label: 'CAPEX, пессимистичный сценарий', scenario: 'pess', key: 'capex', unit: 'руб.' },
  { label: 'OPEX за год, оптимистичный сценарий', scenario: 'opt', key: 'opex', unit: 'руб./год' },
  { label: 'OPEX за год, пессимистичный сценарий', scenario: 'pess', key: 'opex', unit: 'руб./год' },
  { label: 'Годовой эффект, оптимистичный сценарий', scenario: 'opt', key: 'effect', unit: 'руб./год' },
  { label: 'Годовой эффект, пессимистичный сценарий', scenario: 'pess', key: 'effect', unit: 'руб./год' },
  { label: 'Срок окупаемости, оптимистичный сценарий', scenario: 'opt', key: 'payback', unit: 'лет' },
  { label: 'Срок окупаемости, пессимистичный сценарий', scenario: 'pess', key: 'payback', unit: 'лет' },
  { label: 'ROI, оптимистичный сценарий', scenario: 'opt', key: 'roi', unit: '%' },
  { label: 'ROI, пессимистичный сценарий', scenario: 'pess', key: 'roi', unit: '%' },
  { label: 'TCO, оптимистичный сценарий', scenario: 'opt', key: 'tco', unit: 'руб.' },
  { label: 'TCO, пессимистичный сценарий', scenario: 'pess', key: 'tco', unit: 'руб.' },
]

function economyText(row) {
  const value = props.economy?.[row.scenario]?.[row.key]
  const shown = formatMetric(value)
  return shown === '—' ? shown : `${shown} ${row.unit}`
}

function peopleValue(label) {
  if (label === 'Тип решения') return 'Ручные операции'
  if (label === 'Назначение') return 'Персонал предприятия'
  if (label === 'Оценка подбора') return 'Сценарий без робота'
  if (label === 'Стоимость' && props.staffCost !== null && props.staffCost !== '') {
    return `${Number(props.staffCost).toLocaleString('ru-RU')} руб/мес на человека`
  }
  return '—'
}
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Характеристика</th>
          <th v-for="item in items" :key="item.product.id">
            {{ item.product.name }}
            <small v-if="forced.includes(item.product.id)">Добавлено вручную</small>
          </th>
          <th>Без робота</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in compareRows" :key="row.label">
          <th>{{ row.label }}</th>
          <td v-for="item in items" :key="item.product.id">{{ row.value(item) }}</td>
          <td>{{ peopleValue(row.label) }}</td>
        </tr>
        <tr v-if="forced.length">
          <th>Предупреждение</th>
          <td v-for="item in items" :key="item.product.id">
            <template v-if="forced.includes(item.product.id)">
              Не прошло отбор: {{ item.reasons.join('. ') }}
            </template>
          </td>
          <td>—</td>
        </tr>
        <tr v-for="row in economyRows" :key="row.label" class="economy">
          <th>{{ row.label }}</th>
          <td :colspan="items.length">{{ economyText(row) }}</td>
          <td>—</td>
        </tr>
      </tbody>
    </table>
    <p class="note">
      Экономические строки — один расчёт на параметры объекта, поэтому цифра общая для всей подборки.
      Колонка «Без робота» — сценарий, где операции выполняют люди. Стоимость персонала берётся из параметров объекта, остальные показатели сервер не считает.
    </p>
  </div>
</template>

<style scoped>
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

.economy th,
.economy td {
  background: #f7f7ff;
}

.note {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.45;
}
</style>
