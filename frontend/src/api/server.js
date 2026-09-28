async function call(prefix, path, options = {}) {
  let response
  try {
    response = await fetch(`${prefix}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    })
  } catch {
    throw new Error(prefix === '/db' ? 'База не отвечает на порту 8000.' : 'Сервис расчёта не отвечает на порту 7000.')
  }

  const text = await response.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { detail: text.slice(0, 400) }
  }
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : `Ответ ${response.status}`
    throw new Error(detail)
  }
  return data
}

export function dbRequest(path, options) {
  return call('/db', path, options)
}

export function mathRequest(path) {
  return call('/calc', path)
}

const CASE_ID = 1
const ROBOT_ID = 1

function metricPath(name, scenario) {
  const base = `/math/${name}?case_id=${CASE_ID}&robot_id=${ROBOT_ID}&scenario=${scenario}`
  if (name === 'YearEffect' || name === 'PBPeriod' || name === 'ROI') {
    return `${base}&add_inc=0&prev_los=0`
  }
  return base
}

const metricPick = {
  robots: (data) => data?.robot_count,
  capex: (data) => data?.CAPEX,
  opex: (data) => data?.OPEX,
  effect: (data) => data?.year_effect,
  payback: (data) => data?.payback_period,
  roi: (data) => data?.ROI,
  tco: (data) => data?.TCO,
}

export function formatMetric(value) {
  if (value === null || value === undefined || value === '') return '—'
  const number = Number(value)
  if (Number.isNaN(number)) return '—'
  return number.toLocaleString('ru-RU', { maximumFractionDigits: 1 })
}

const metricTitles = {
  robots: 'Число роботов',
  capex: 'CAPEX',
  opex: 'OPEX',
  effect: 'Годовой эффект',
  payback: 'Окупаемость',
  roi: 'ROI',
  tco: 'TCO',
}

function economySnapshot(economy) {
  return { opt: { ...economy.opt }, pess: { ...economy.pess } }
}

export async function calculateObject(type, params, onProgress) {
  const jobs = ['opt', 'pess'].flatMap((scenario) => Object.keys(metricPick).map((key) => ({ scenario, key })))
  const report = (done, label, economy) => {
    onProgress?.({ done, total: jobs.length, label, economy: economySnapshot(economy) })
  }
  const economy = { opt: {}, pess: {} }
  report(0, 'Записываем параметры объекта', economy)
  await dbRequest('/dataset', {
    method: 'POST',
    body: JSON.stringify(datasetPayload(type, params, CASE_ID)),
  })
  let failure = ''
  let done = 0
  const queue = [...jobs]
  async function next() {
    const job = queue.shift()
    if (!job) return
    const pathName = {
      robots: 'robots',
      capex: 'CAPEX',
      opex: 'OPEX',
      effect: 'YearEffect',
      payback: 'PBPeriod',
      roi: 'ROI',
      tco: 'TCO',
    }[job.key]
    const scenarioName = job.scenario === 'opt' ? 'оптимистичный' : 'пессимистичный'
    report(done, `${metricTitles[job.key]}, ${scenarioName} сценарий`, economy)
    try {
      const data = await mathRequest(metricPath(pathName, job.scenario))
      const value = metricPick[job.key](data)
      economy[job.scenario][job.key] = value === undefined ? null : value
    } catch (error) {
      economy[job.scenario][job.key] = null
      if (!failure) {
        const text = error?.message || 'Не удалось посчитать экономику.'
        failure = text.length < 180 ? text : 'Сервис расчёта не смог посчитать показатели по этим параметрам.'
      }
    }
    done += 1
    report(done, done === jobs.length ? 'Готово' : `${metricTitles[job.key]} посчитан`, economy)
    await next()
  }
  await Promise.all([next(), next()])
  const values = Object.values(economy).flatMap((scenario) => Object.values(scenario))
  return {
    economy,
    error: values.every((value) => value == null) ? failure : '',
  }
}

export const serverObjectName = {
  warehouse: 'Склад',
  airport: 'Аэропорт',
  medical: 'Медучреждение',
}

export function datasetPayload(type, params, caseId) {
  const data = {}
  type.fields.forEach((field) => {
    const value = params[field.key]
    const shown = field.type === 'select'
      ? field.options.find((option) => option.id === value)?.label || value
      : value
    data[field.label] = {
      unit: field.unit || '',
      base: String(shown ?? ''),
      min: field.min == null ? '' : String(field.min),
      max: field.max == null ? '' : String(field.max),
      note: field.source || '',
      scenario: String(shown ?? ''),
    }
  })
  data['Процесс'] = {
    unit: '',
    base: String(params.process || ''),
    min: '',
    max: '',
    note: '',
    scenario: String(params.process || ''),
  }
  return {
    case_id: Number(caseId),
    object_type: serverObjectName[type.id] || type.title,
    source_file: 'frontend',
    data,
  }
}
