<script setup>
import { computed } from 'vue'
import { filterGroups, optionsFor } from '../data/catalog'

const filters = defineModel({ type: Object, required: true })

const chips = computed(() => {
  const selected = []
  for (const group of filterGroups) {
    for (const field of group.fields || []) {
      for (const value of filters.value[field.key]) {
        selected.push({ key: field.key, value })
      }
    }
  }
  return selected
})

function toggle(key, value) {
  const list = filters.value[key]
  filters.value[key] = list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

function removeChip(chip) {
  filters.value[chip.key] = filters.value[chip.key].filter((item) => item !== chip.value)
}
</script>

<template>
  <aside class="filters">
    <h2>Фильтры</h2>
    <div v-if="chips.length" class="chips">
      <button v-for="chip in chips" :key="chip.key + chip.value" type="button" class="chip" @click="removeChip(chip)">
        {{ chip.value }}
        <span aria-hidden="true">×</span>
      </button>
    </div>

    <section v-for="group in filterGroups" :key="group.title" class="group">
      <h3>{{ group.title }}</h3>

      <div v-for="field in group.fields || []" :key="field.key" class="field">
        <p>{{ field.label }}</p>
        <label v-for="option in optionsFor(field.key)" :key="option">
          <input
            type="checkbox"
            :checked="filters[field.key].includes(option)"
            @change="toggle(field.key, option)"
          />
          {{ option }}
        </label>
      </div>

      <label v-for="range in group.ranges || []" :key="range.key" class="range">
        <span>{{ range.label }} <b>до {{ filters[range.key] }} {{ range.unit }}</b></span>
        <input v-model.number="filters[range.key]" type="range" :min="range.min" :max="range.max" />
      </label>

      <label v-for="flag in group.flags || []" :key="flag.key" class="flag">
        <input v-model="filters[flag.key]" type="checkbox" />
        {{ flag.label }}
      </label>
    </section>
  </aside>
</template>

<style scoped>
.filters {
  box-sizing: border-box;
  width: 280px;
  flex: none;
  padding: 16px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
}

h2 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}

h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 16px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border: 0;
  border-radius: 8px;
  background: #f5f5f5;
  color: var(--text);
  font-size: 14px;
  cursor: pointer;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.field,
.range {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field p,
.range span,
.flag {
  margin: 0;
  font-size: 14px;
  line-height: 1.4;
}

.range b {
  font-weight: 400;
  color: var(--muted);
}

label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

input[type='checkbox'] {
  width: 16px;
  height: 16px;
  accent-color: #2c2c2c;
}

input[type='range'] {
  width: 100%;
  accent-color: #2c2c2c;
}

@media (max-width: 900px) {
  .filters {
    width: 100%;
  }
}
</style>
