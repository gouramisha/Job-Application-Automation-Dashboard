/** Dates arrive as ISO strings; every one of these tolerates null. */

export function formatDate(value, options = {}) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric', ...options })
}

export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString(undefined, {
    day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}

export function formatShortDate(value) {
  return formatDate(value, { year: undefined })
}

/** '3 days ago', 'in 2 weeks'. Falls back to an absolute date past a month. */
export function relativeDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  const days = Math.round((date - new Date().setHours(0, 0, 0, 0)) / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Tomorrow'
  if (days === -1) return 'Yesterday'
  if (Math.abs(days) < 30) {
    return days > 0 ? `in ${days} days` : `${Math.abs(days)} days ago`
  }
  return formatDate(value)
}

export function formatBytes(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function initials(name = '') {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('') || '?'
}

export function splitCsv(value = '') {
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}
