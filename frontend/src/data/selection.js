import { products } from './catalog'

const source = 'Демонстрационный набор'

export const objectTypes = [
  {
    id: 'warehouse',
    title: 'Склад',
    catalogObject: 'Склад',
    lead: 'Приёмка, перемещение и комплектация',
    processes: [
      { id: 'any', label: 'Любой подходящий процесс' },
      { id: 'intra', label: 'Внутрискладская логистика', purposes: ['Внутрискладская логистика'] },
      { id: 'move', label: 'Перемещение грузов', purposes: ['Перемещение грузов'] },
      { id: 'pick', label: 'Комплектация', purposes: ['Комплектация'] },
    ],
    fields: [
      field('area', 'Площадь рабочих зон', 'м²', { min: 200, max: 500000, hint: 'Например, 15 000', group: 'Объект', demo: 15000 }),
      field('zones', 'Число рабочих зон', 'шт.', { min: 1, max: 80, hint: 'Приёмка, хранение, отгрузка', group: 'Объект', demo: 4 }),
      field('hoursPerDay', 'Режим работы', 'ч/сутки', { min: 1, max: 24, hint: 'Длительность смены или суток', group: 'Объект', demo: 16 }),
      field('daysPerWeek', 'Рабочих дней', 'дн/нед', { min: 1, max: 7, group: 'Объект', demo: 6 }),
      field('inbound', 'Входящие операции', 'оп/сутки', { min: 0, max: 100000, group: 'Операции', demo: 400 }),
      field('internal', 'Внутрискладские операции', 'оп/сутки', { min: 0, max: 100000, group: 'Операции', demo: 900 }),
      field('outbound', 'Исходящие операции', 'оп/сутки', { min: 0, max: 100000, group: 'Операции', demo: 500 }),
      field('storageType', 'Тип хранения', '', { type: 'select', group: 'Операции', demo: 'rack', options: [
        { id: 'rack', label: 'Стеллажное' },
        { id: 'floor', label: 'Напольное' },
        { id: 'mezz', label: 'Мезонин' },
      ] }),
      field('sku', 'Количество SKU', 'шт.', { min: 1, max: 1000000, group: 'Груз', demo: 8000 }),
      field('unitMass', 'Средняя масса грузовой единицы', 'кг', { min: 0.1, max: 2000, hint: 'Сравнивается с грузоподъёмностью', group: 'Груз', demo: 40 }),
      field('unitLength', 'Длина грузовой единицы', 'мм', { required: false, min: 10, max: 4000, hint: 'Габарит для сверки с роботом', group: 'Груз', demo: 800 }),
      field('staffCount', 'Численность персонала', 'чел.', { min: 1, max: 5000, hint: 'Нужна для будущего расчёта экономики', group: 'Персонал', demo: 24 }),
      field('staffCost', 'Стоимость персонала', 'руб/мес', { min: 0, max: 2000000, hint: 'На одного сотрудника, для расчёта экономики', group: 'Персонал', demo: 80000 }),
      field('productivity', 'Производительность текущего процесса', 'оп/ч', { min: 1, max: 100000, group: 'Ограничения', demo: 120 }),
      field('routeLength', 'Протяжённость маршрутов', 'м', { min: 1, max: 20000, group: 'Ограничения', demo: 180 }),
      field('freeArea', 'Свободная площадь под технику', 'м²', { required: false, min: 0, max: 500000, group: 'Ограничения', demo: 2000 }),
      field('layout', 'Ограничения планировки', '', { type: 'select', group: 'Ограничения', demo: 'narrow', options: [
        { id: 'none', label: 'Нет особых ограничений' },
        { id: 'narrow', label: 'Узкие проходы' },
        { id: 'low', label: 'Низкие потолки' },
      ] }),
    ],
  },
  {
    id: 'airport',
    title: 'Аэропорт',
    catalogObject: 'Аэропорт',
    lead: 'Перрон, терминал и грузовая зона',
    processes: [
      { id: 'any', label: 'Любой подходящий процесс' },
      { id: 'inspect', label: 'Инспекция территории', purposes: ['Инспекция территории'] },
      { id: 'move', label: 'Перемещение грузов', purposes: ['Перемещение грузов'] },
    ],
    fields: [
      field('zone', 'Зона операции', '', { type: 'select', group: 'Объект', demo: 'cargo', options: [
        { id: 'apron', label: 'Перрон' },
        { id: 'terminal', label: 'Пассажирский терминал' },
        { id: 'cargo', label: 'Грузовая зона' },
      ] }),
      field('setting', 'Где проходит операция', '', { type: 'select', group: 'Объект', demo: 'both', options: [
        { id: 'indoor', label: 'Закрытые зоны' },
        { id: 'outdoor', label: 'Открытые зоны' },
        { id: 'both', label: 'Закрытые и открытые зоны' },
      ] }),
      field('hoursPerDay', 'Режим работы', 'ч/сутки', { min: 1, max: 24, group: 'Объект', demo: 18 }),
      field('daysPerWeek', 'Рабочих дней', 'дн/нед', { min: 1, max: 7, group: 'Объект', demo: 7 }),
      field('flow', 'Пассажиро- или грузопоток', 'ед/сутки', { min: 0, max: 1000000, group: 'Операции', demo: 120 }),
      field('operations', 'Количество операций', 'оп/сутки', { min: 0, max: 100000, group: 'Операции', demo: 300 }),
      field('peak', 'Пиковая нагрузка', 'оп/ч', { min: 1, max: 100000, group: 'Операции', demo: 40 }),
      field('routeLength', 'Протяжённость маршрутов', 'м', { min: 1, max: 30000, group: 'Ограничения', demo: 600 }),
      field('unitMass', 'Масса перемещаемого объекта', 'кг', { min: 0.1, max: 5000, hint: 'Сравнивается с грузоподъёмностью', group: 'Груз', demo: 4 }),
      field('unitLength', 'Длина перемещаемого объекта', 'мм', { required: false, min: 10, max: 20000, group: 'Груз', demo: 400 }),
      field('staffCount', 'Численность персонала', 'чел.', { min: 1, max: 5000, hint: 'Нужна для будущего расчёта экономики', group: 'Персонал', demo: 10 }),
      field('security', 'Требования безопасности', '', { type: 'select', group: 'Ограничения', demo: 'high', options: [
        { id: 'standard', label: 'Стандартные' },
        { id: 'high', label: 'Повышенные' },
      ] }),
    ],
  },
  {
    id: 'medical',
    title: 'Медицинское учреждение',
    catalogObject: 'Медицинское учреждение',
    lead: 'Перевозка белья, питания и медикаментов',
    processes: [
      { id: 'any', label: 'Любой подходящий процесс' },
      { id: 'delivery', label: 'Внутренняя доставка', purposes: ['Внутренняя доставка'] },
    ],
    fields: [
      field('facility', 'Тип учреждения', '', { type: 'select', group: 'Объект', demo: 'hospital', options: [
        { id: 'hospital', label: 'Больница' },
        { id: 'clinic', label: 'Поликлиника' },
        { id: 'lab', label: 'Лаборатория' },
      ] }),
      field('area', 'Площадь', 'м²', { min: 100, max: 500000, group: 'Объект', demo: 25000 }),
      field('floors', 'Этажность', 'эт.', { min: 1, max: 40, group: 'Объект', demo: 6 }),
      field('hoursPerDay', 'Режим работы', 'ч/сутки', { min: 1, max: 24, group: 'Объект', demo: 12 }),
      field('trips', 'Перевозок в сутки', 'шт.', { min: 0, max: 100000, hint: 'Грузы, бельё, питание, медикаменты или отходы', group: 'Операции', demo: 180 }),
      field('cargoKind', 'Что перевозят', '', { type: 'select', group: 'Операции', demo: 'mixed', options: [
        { id: 'linen', label: 'Бельё и питание' },
        { id: 'meds', label: 'Медикаменты' },
        { id: 'waste', label: 'Отходы' },
        { id: 'mixed', label: 'Смешанные перевозки' },
      ] }),
      field('unitMass', 'Средняя масса груза', 'кг', { min: 0.1, max: 500, hint: 'Сравнивается с грузоподъёмностью', group: 'Груз', demo: 12 }),
      field('routeLength', 'Протяжённость маршрутов', 'м', { min: 1, max: 10000, group: 'Ограничения', demo: 220 }),
      field('elevators', 'Лифты на маршруте', '', { type: 'select', group: 'Ограничения', demo: 'yes', options: [
        { id: 'yes', label: 'Есть' },
        { id: 'no', label: 'Нет' },
      ] }),
      field('sanitation', 'Санитарная обработка', '', { type: 'select', group: 'Ограничения', demo: 'strict', options: [
        { id: 'standard', label: 'Стандартная' },
        { id: 'strict', label: 'Усиленная' },
      ] }),
      field('staffCount', 'Численность персонала', 'чел.', { min: 1, max: 5000, hint: 'Нужна для будущего расчёта экономики', group: 'Персонал', demo: 15 }),
      field('access', 'Доступ в зоны', '', { type: 'select', group: 'Ограничения', demo: 'limited', options: [
        { id: 'open', label: 'Служебные зоны открыты' },
        { id: 'limited', label: 'Доступ ограничен' },
      ] }),
    ],
  },
]

function field(key, label, unit, extra) {
  return {
    key,
    label,
    unit,
    type: extra.type || 'number',
    required: extra.required !== false,
    min: extra.min,
    max: extra.max,
    hint: extra.hint || '',
    group: extra.group,
    demo: extra.demo,
    source,
    options: extra.options || [],
  }
}

export function getType(typeId) {
  return objectTypes.find((item) => item.id === typeId) || objectTypes[0]
}

export function demoParams(typeId) {
  const type = getType(typeId)
  const params = { process: 'any' }
  type.fields.forEach((item) => {
    params[item.key] = item.demo
  })
  return params
}

export function validateParams(typeId, params) {
  const type = getType(typeId)
  const errors = []
  if (!type.processes.some((item) => item.id === params.process)) {
    errors.push({ key: 'process', message: 'Выберите процесс' })
  }
  type.fields.forEach((item) => {
    const value = params[item.key]
    const empty = value === '' || value === null || value === undefined
    if (empty) {
      if (item.required) errors.push({ key: item.key, message: `Укажите: ${item.label.toLowerCase()}` })
      return
    }
    if (item.type === 'select') {
      if (!item.options.some((option) => option.id === value)) {
        errors.push({ key: item.key, message: `Выберите значение: ${item.label.toLowerCase()}` })
      }
      return
    }
    const number = Number(value)
    if (Number.isNaN(number)) {
      errors.push({ key: item.key, message: `${item.label}: нужно число` })
      return
    }
    if (number < item.min || number > item.max) {
      errors.push({
        key: item.key,
        message: `${item.label}: от ${item.min} до ${item.max}${item.unit ? ` ${item.unit}` : ''}`,
      })
    }
  })
  return errors
}

export function templateCsv(typeId) {
  const type = getType(typeId)
  const demo = demoParams(typeId)
  const keys = ['process', ...type.fields.map((item) => item.key)]
  const labels = ['Процесс', ...type.fields.map((item) => item.label)]
  const values = keys.map((key) => demo[key])
  return `\uFEFF${[keys.join(';'), labels.join(';'), values.join(';')].join('\n')}`
}

export function parseCsv(text, typeId) {
  const type = getType(typeId)
  const lines = text
    .replace(/^\uFEFF/, '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  if (lines.length < 2) return { error: 'В файле нет строки с данными' }
  const keys = lines[0].split(';').map((item) => item.trim())
  const expected = ['process', ...type.fields.map((item) => item.key)]
  const missing = expected.filter((key) => !keys.includes(key))
  if (missing.length) return { error: 'Это не шаблон выбранного типа объекта. Скачайте шаблон и заполните его.' }
  const dataLine = lines.find((line, index) => index > 0 && !line.startsWith('Процесс') && !line.startsWith('Площадь'))
  if (!dataLine) return { error: 'Не найдена строка со значениями' }
  const cells = dataLine.split(';')
  const params = {}
  keys.forEach((key, index) => {
    params[key] = cells[index]?.trim() ?? ''
  })
  type.fields.forEach((item) => {
    if (item.type === 'number' && params[item.key] !== '') params[item.key] = Number(params[item.key].replace(',', '.'))
  })
  return { params }
}

export function matchProducts(typeId, params, list = products) {
  const type = getType(typeId)
  const process = type.processes.find((item) => item.id === params.process)
  const matched = []
  const excluded = []

  list.forEach((product) => {
    const blockers = hardLimits(type, params, process, product)
    if (blockers.length) {
      excluded.push({ product, reasons: blockers })
      return
    }
    matched.push(scoreProduct(type, params, product))
  })

  matched.sort((a, b) => b.score - a.score || a.product.name.localeCompare(b.product.name, 'ru'))
  excluded.sort((a, b) => a.product.name.localeCompare(b.product.name, 'ru'))
  return { matched, excluded }
}

function hardLimits(type, params, process, product) {
  const reasons = []
  if (!product.objects.includes(type.catalogObject)) {
    reasons.push(`Не поддерживает объект «${type.catalogObject}»`)
  }
  if (process?.purposes && !process.purposes.includes(product.purpose)) {
    reasons.push(`Назначение «${product.purpose}» не закрывает процесс «${process.label}»`)
  }
  if (product.status === 'Снят с поставки') {
    reasons.push('Снят с поставки, заказать нельзя')
  }
  const mass = Number(params.unitMass)
  if (!Number.isNaN(mass) && mass > product.payload) {
    reasons.push(`Грузоподъёмность ${product.payload} кг меньше массы груза ${mass} кг`)
  }
  if (type.id === 'airport' && params.setting === 'outdoor' && settingOf(product) === 'indoor') {
    reasons.push('Рассчитан на закрытые помещения, а операция идёт на открытой зоне')
  }
  if (type.id === 'airport' && params.setting === 'indoor' && settingOf(product) === 'outdoor') {
    reasons.push('Рассчитан на открытую территорию, а операция идёт в закрытой зоне')
  }
  if (type.id === 'medical' && Number(params.floors) > 1 && params.elevators === 'no') {
    reasons.push('Несколько этажей и нет лифта: робот не пройдёт маршрут')
  }
  return reasons
}

function settingOf(product) {
  return product.solutionType === 'БАС' ? 'outdoor' : 'indoor'
}

function scoreProduct(type, params, product) {
  const factors = [
    payloadFactor(params, product),
    autonomyFactor(params, product),
    casesFactor(product),
    dataFactor(product),
    statusFactor(product),
    infraFactor(type, params, product),
  ]
  const known = factors.filter((item) => item.points !== null)
  const points = known.reduce((sum, item) => sum + item.points, 0)
  const max = known.reduce((sum, item) => sum + item.weight, 0)
  const missing = factors.filter((item) => item.points === null).map((item) => item.note)
  const limits = factors.flatMap((item) => item.limits || [])
  return {
    product,
    score: max ? Math.round((points / max) * 100) : 0,
    needsCheck: missing.length > 0 || !product.confirmed,
    reasons: factors.flatMap((item) => item.reasons || []),
    limits: [...limits, ...contextNotes(type, params, product)],
    missing,
    factors,
  }
}

function payloadFactor(params, product) {
  const mass = Number(params.unitMass)
  const weight = 30
  if (!mass) {
    return { id: 'payload', label: 'Запас грузоподъёмности', weight, points: null, note: 'Не задана масса груза' }
  }
  const ratio = product.payload / mass
  const points = ratio >= 1.5 && ratio <= 10 ? 30 : 21
  return {
    id: 'payload',
    label: 'Запас грузоподъёмности',
    weight,
    points,
    reasons: [`Грузоподъёмность ${product.payload} кг покрывает груз ${mass} кг`],
    limits: ratio > 10 ? ['Запас грузоподъёмности большой: робот заметно мощнее задачи'] : [],
  }
}

function autonomyFactor(params, product) {
  const shift = Number(params.hoursPerDay)
  const weight = 20
  if (!shift) {
    return { id: 'autonomy', label: 'Автономность на смену', weight, points: null, note: 'Не задана длительность работы' }
  }
  if (product.autonomy >= shift) {
    return {
      id: 'autonomy',
      label: 'Автономность на смену',
      weight,
      points: 20,
      reasons: [`Автономность ${product.autonomy} ч покрывает режим ${shift} ч`],
    }
  }
  return {
    id: 'autonomy',
    label: 'Автономность на смену',
    weight,
    points: Math.max(4, Math.round((20 * product.autonomy) / shift)),
    limits: [`Автономность ${product.autonomy} ч меньше режима ${shift} ч: понадобится подзарядка`],
  }
}

function casesFactor(product) {
  return {
    id: 'cases',
    label: 'Реализованные кейсы',
    weight: 15,
    points: product.hasCases ? 15 : 4,
    reasons: product.hasCases ? ['Есть реализованный кейс'] : [],
    limits: product.hasCases ? [] : ['Реализованных кейсов в каталоге нет'],
  }
}

function dataFactor(product) {
  return {
    id: 'data',
    label: 'Подтвержденность данных',
    weight: 15,
    points: product.confirmed ? 15 : 6,
    reasons: product.confirmed ? ['Характеристики подтверждены'] : [],
    limits: product.confirmed ? [] : ['Часть характеристик не подтверждена'],
  }
}

function statusFactor(product) {
  const onOrder = product.status === 'Под заказ'
  return {
    id: 'status',
    label: 'Доступность',
    weight: 10,
    points: onOrder ? 6 : 10,
    reasons: [`Статус: ${product.status}`],
    limits: onOrder ? ['Поставка под заказ, срок нужно уточнять'] : [],
  }
}

function infraFactor(type, params, product) {
  const weight = 10
  const limits = []
  let points = 10
  if (type.id === 'warehouse' && params.layout === 'narrow' && !product.infra.includes('Покрытие и проходы')) {
    points = 4
    limits.push('Для узких проходов в карточке нет требования к покрытию и проездам')
  }
  if (type.id === 'airport' && params.setting === 'both' && settingOf(product) === 'indoor') {
    points = 6
    limits.push('На открытой части зоны применение нужно отдельно подтвердить')
  }
  return {
    id: 'infra',
    label: 'Инфраструктура объекта',
    weight,
    points,
    reasons: points === 10 ? ['Явных противоречий с инфраструктурой нет'] : [],
    limits,
  }
}

function contextNotes(type, params, product) {
  const notes = []
  if (params.unitLength) notes.push('Габарит груза нужно сверить с габаритами робота по паспорту')
  if (type.id === 'warehouse' && params.layout === 'low') {
    notes.push('При низких потолках высоту робота нужно сверить с проёмами')
  }
  if (type.id === 'medical' && Number(params.floors) > 1 && params.elevators === 'yes') {
    notes.push('Маршрут проходит через лифты, это нужно подтвердить у поставщика')
  }
  if (type.id === 'medical' && params.sanitation === 'strict') {
    notes.push('Усиленная санитарная обработка в каталоге отдельно не описана')
  }
  if (type.id === 'airport' && params.security === 'high') {
    notes.push('Повышенные требования безопасности нужно согласовать отдельно')
  }
  if (product.infra.length) notes.push(`Инфраструктура: ${product.infra.join(', ')}`)
  return notes
}

export const compareRows = [
  { label: 'Производитель', value: (item) => item.product.company },
  { label: 'Тип решения', value: (item) => item.product.solutionType },
  { label: 'Назначение', value: (item) => item.product.purpose },
  { label: 'Страна', value: (item) => item.product.country },
  { label: 'Статус', value: (item) => item.product.status },
  { label: 'Грузоподъёмность', value: (item) => `${item.product.payload} кг` },
  { label: 'Навигация', value: (item) => item.product.navigation },
  { label: 'Автономность', value: (item) => `${item.product.autonomy} ч` },
  { label: 'Стоимость', value: (item) => `${item.product.price.toLocaleString('ru-RU')} тыс. руб` },
  { label: 'Приобретение', value: (item) => item.product.acquisition },
  { label: 'Срок службы', value: (item) => `${item.product.serviceLife} лет` },
  { label: 'Оценка подбора', value: (item) => (item.score === null ? 'Вне подборки' : `${item.score} из 100`) },
]
