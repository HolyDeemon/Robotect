<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { mathRequest } from '../../api/server'

const props = defineProps({
  userId: { type: [String, Number], default: 'guest' },
  objectType: { type: String, required: true },
  robotCount: { type: Number, default: 4 },
  caseId: { type: Number, default: 1 },
  robotId: { type: Number, default: 1 },
  economy: { type: Object, default: null },
})

const canvas = ref(null)
const status = ref('Подключение к симуляции…')
const connected = ref(false)
const kpi = ref(null)
const robots = ref([])
const map = ref(null)
const economics = ref({
  robots: null,
  capex: null,
  opex: null,
  effect: null,
  payback: null,
  roi: null,
  tco: null,
})
const economyNote = ref('')
const shownEconomy = computed(() => {
  const saved = props.economy?.opt
  if (!saved) return economics.value
  return {
    robots: saved.robots ?? economics.value.robots,
    capex: saved.capex,
    opex: saved.opex,
    effect: saved.effect,
    payback: saved.payback,
    roi: saved.roi,
    tco: saved.tco,
  }
})

const cards = [
  { key: 'operations_done', label: 'Выполнено операций', unit: 'шт.' },
  { key: 'shift_progress_pct', label: 'Прогресс смены', unit: '%' },
  { key: 'utilization_pct', label: 'Загрузка роботов', unit: '%' },
  { key: 'idle_pct', label: 'Простои', unit: '%' },
  { key: 'task_queue_len', label: 'Очередь задач', unit: 'шт.' },
  { key: 'savings_rub', label: 'Накопленная экономия', unit: 'руб.' },
  { key: 'total_distance_m', label: 'Пройденный путь', unit: 'м.' },
  { key: 'avg_battery_pct', label: 'Средний заряд АКБ', unit: '%' },
]

const side = [
  { key: 'robots', label: 'Кол-во роботов', unit: 'шт.' },
  { key: 'capex', label: 'CAPEX', unit: 'руб.' },
  { key: 'opex', label: 'OPEX (годовой)', unit: 'руб.' },
  { key: 'effect', label: 'Годовой эффект', unit: 'руб.' },
  { key: 'payback', label: 'Срок окупаемости', unit: 'лет' },
  { key: 'roi', label: 'ROI', unit: '%' },
  { key: 'tco', label: 'TCO', unit: 'руб.' },
]

const tileColors = {
  0: '#f7f8fc',
  1: '#9aa0d6',
  2: '#ffffff',
  3: '#bdf2de',
  4: '#7dcea0',
  5: '#6366ff',
  6: '#f0b429',
  7: '#2c2c2c',
}

let socket = null
let finished = false

watch(() => [props.objectType, props.userId, props.robotCount], connect)

function shown(value) {
  if (value === null || value === undefined || value === '') return '—'
  const number = Number(value)
  if (Number.isNaN(number)) return '—'
  return number.toLocaleString('ru-RU', { maximumFractionDigits: 1 })
}

function kpiValue(key) {
  return shown(kpi.value?.[key])
}

function connect() {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${protocol}://${location.host}/calc/ws/${encodeURIComponent(props.userId || 'guest')}?case_id=${props.caseId}&robot_id=${props.robotId}`
  if (socket && socket.url === url && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return
  }
  socket?.close()
  finished = false
  kpi.value = null
  robots.value = []
  map.value = null
  connected.value = false
  status.value = 'Подключение к симуляции…'
  const link = new WebSocket(url)
  socket = link
  link.onopen = () => {
    connected.value = true
    status.value = 'Соединение открыто, ждём карту объекта.'
    link.send(JSON.stringify({
      object_type: props.objectType,
      n_robots: props.robotCount,
      n_steps: 300,
      time_scale: 60,
      seed: 42,
      saving_per_operation: 0,
    }))
  }
  link.onmessage = (event) => {
    let message
    try {
      message = JSON.parse(event.data)
    } catch {
      status.value = 'Сервер прислал непонятный ответ.'
      return
    }
    if (message.type === 'map') {
      map.value = message
      robots.value = message.robots || []
      status.value = props.economy
        ? 'Роботы на карте.'
        : 'Роботы поехали. Экономика справа появится, когда прогон закончится.'
      nextTick(draw)
      return
    }
    if (message.type === 'state') {
      kpi.value = message.kpi || null
      robots.value = message.robots || []
      if (message.robots?.length) economics.value.robots = message.robots.length
      nextTick(draw)
      return
    }
    if (message.type === 'started') {
      status.value = 'Симуляция идёт.'
      return
    }
    if (message.type === 'error') {
      status.value = message.message || 'Сервер симуляции вернул ошибку.'
      connected.value = false
      return
    }
    if (message.type === 'stopped' || message.type === 'done') {
      finished = true
      status.value = message.type === 'done'
        ? 'Прогон закончился. На карте последний кадр, справа — экономика объекта.'
        : 'Симуляция остановлена.'
      connected.value = false
      if (message.type === 'done' && !props.economy) loadEconomics()
    }
  }
  link.onerror = () => {
    status.value = 'Сервис симуляции не отвечает. Он должен быть запущен на порту 7000.'
    connected.value = false
  }
  link.onclose = (event) => {
    connected.value = false
    if (finished) return
    if (event.reason) status.value = event.reason
    else if (!kpi.value) status.value = 'Сервер закрыл симуляцию. Обычно так бывает, если у кейса нет датасета или робот не найден.'
  }
}

function draw() {
  const board = canvas.value
  const grid = map.value?.grid
  if (!board || !grid?.length) return
  const rows = grid.length
  const cols = grid[0].length
  const box = board.parentElement
  const width = Math.max(box?.clientWidth || 640, 320)
  const scale = Math.min(width / cols, 520 / rows)
  board.width = Math.floor(cols * scale)
  board.height = Math.floor(rows * scale)
  const ctx = board.getContext('2d')
  ctx.clearRect(0, 0, board.width, board.height)
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      ctx.fillStyle = tileColors[grid[row][col]] || '#fff'
      ctx.fillRect(col * scale, row * scale, scale + 0.5, scale + 0.5)
    }
  }
  robots.value.forEach((robot) => {
    const x = Number(robot.x) * scale
    const y = Number(robot.y) * scale
    if (robot.path?.length) {
      ctx.strokeStyle = robot.color || '#6366ff'
      ctx.lineWidth = Math.max(scale * 0.15, 1)
      ctx.beginPath()
      ctx.moveTo(x, y)
      robot.path.forEach(([row, col]) => {
        ctx.lineTo((Number(col) + 0.5) * scale, (Number(row) + 0.5) * scale)
      })
      ctx.stroke()
    }
    ctx.fillStyle = robot.color || '#6366ff'
    ctx.beginPath()
    ctx.arc(x, y, Math.max(scale * 0.45, 7), 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#1e1e1e'
    ctx.lineWidth = 1
    ctx.stroke()
  })
}

async function loadEconomics() {
  economyNote.value = ''
  const query = `case_id=${props.caseId}&robot_id=${props.robotId}&scenario=opt`
  const calls = [
    ['capex', `/math/CAPEX?${query}`],
    ['opex', `/math/OPEX?${query}`],
    ['effect', `/math/YearEffect?${query}&add_inc=0&prev_los=0`],
    ['payback', `/math/PBPeriod?${query}&add_inc=0&prev_los=0`],
    ['roi', `/math/ROI?${query}&add_inc=0&prev_los=0`],
    ['tco', `/math/TCO?${query}`],
  ]
  const results = await Promise.all(calls.map(async ([key, path]) => {
    try {
      const data = await mathRequest(path)
      const value = {
        capex: data?.CAPEX,
        opex: data?.OPEX,
        effect: data?.year_effect,
        payback: data?.payback_period,
        roi: data?.ROI,
        tco: data?.TCO,
      }[key] ?? null
      return [key, value]
    } catch {
      return [key, null]
    }
  }))
  results.forEach(([key, value]) => {
    economics.value[key] = value
  })
  if (results.every(([, value]) => value === null)) {
    economyNote.value = 'Сервис расчёта не вернул CAPEX, OPEX и остальные показатели.'
  }
}

connect()

onUnmounted(() => socket?.close())
</script>

<template>
  <div class="sim">
    <div class="kpis">
      <article v-for="card in cards" :key="card.key">
        <span>{{ card.label }}</span>
        <strong>{{ kpiValue(card.key) }}</strong>
        <small>{{ card.unit }}</small>
      </article>
    </div>
    <div class="stage">
      <div class="map-wrap">
        <div class="map">
          <canvas ref="canvas"></canvas>
          <p v-if="!map" class="wait">{{ status }}</p>
        </div>
        <ul class="legend">
          <li><i class="shelf"></i> стеллаж</li>
          <li><i class="road"></i> проезд</li>
          <li><i class="pick"></i> забор</li>
          <li><i class="drop"></i> выдача</li>
          <li><i class="charge"></i> зарядка</li>
        </ul>
      </div>
      <aside>
        <article v-for="item in side" :key="item.key">
          <span>{{ item.label }}</span>
          <strong>{{ shown(shownEconomy[item.key]) }}</strong>
          <small>{{ item.unit }}</small>
        </article>
      </aside>
    </div>
    <p class="status" :class="{ ok: connected }">{{ status }}</p>
    <p v-if="economyNote" class="status">{{ economyNote }}</p>
    <button v-if="!connected" type="button" @click="connect">Подключить снова</button>
  </div>
</template>

<style scoped>
.kpis,
aside {
  display: grid;
  gap: 10px;
}

.kpis {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kpis article,
aside article {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #eef0ff;
}

aside article {
  background: #f4f1ff;
}

.kpis span,
aside span,
.kpis small,
aside small {
  color: var(--muted);
  font-size: 13px;
}

.kpis strong,
aside strong {
  font-size: 22px;
  font-weight: 650;
}

.stage {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 16px;
  margin-top: 16px;
}

.map {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 360px;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.wait {
  position: absolute;
  max-width: 360px;
  margin: 0;
  color: var(--text);
  font-size: 14px;
  line-height: 1.45;
  text-align: center;
}

canvas {
  display: block;
  max-width: 100%;
  height: auto;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  color: var(--muted);
  font-size: 13px;
}

.legend li {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend i {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.shelf { background: #9aa0d6; }
.road { background: #bdf2de; }
.pick { background: #6366ff; }
.drop { background: #f0b429; }
.charge { background: #7dcea0; }

.status {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 14px;
}

.status.ok {
  color: #146c43;
}

button {
  height: 40px;
  margin-top: 12px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}

@media (max-width: 900px) {
  .kpis,
  .stage {
    grid-template-columns: 1fr 1fr;
  }

  .stage {
    grid-template-columns: 1fr;
  }
}
</style>
