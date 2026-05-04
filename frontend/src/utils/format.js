/**
 * display formatting helpers
 */

/** 12500 → "12.5K", 1200000 → "1.2M" */
export function fmtNumber(n) {
  if (n === undefined || n === null) return '—'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

/** "2024-05-20T12:00:00Z" → "20 May 2024" */
export function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day:   '2-digit',
    month: 'short',
    year:  'numeric',
  })
}

/** 0.734 → "73%" */
export function fmtPercent(ratio) {
  if (ratio === null || ratio === undefined) return '—'
  return `${Math.round(ratio * 100)}%`
}

/**
 * Return Tailwind-style class suffix based on label.
 * "Active" → "green", "Moderate" → "amber", "Inactive" → "red"
 */
export function labelColor(label) {
  if (!label) return 'muted'
  const l = label.toLowerCase()
  if (l === 'active')   return 'green'
  if (l === 'moderate') return 'amber'
  return 'red'
}

/** severity string → colour key */
export function severityColor(severity) {
  if (severity === 'high')   return 'red'
  if (severity === 'medium') return 'amber'
  return 'blue'
}
