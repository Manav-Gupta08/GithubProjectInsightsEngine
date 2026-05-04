/**
 * Generic search bar that validates "owner/repo" format locally
 * before calling onSubmit. Optionally renders a second input for
 * compare mode when `dual` prop is true.
 */

import { useState } from 'react'
import styles from './SearchBar.module.css'

function validateSlug(slug) {
  const s = slug.trim()
  if (!s) return 'Please enter a repository.'
  if (s.split('/').length !== 2 || s.startsWith('/') || s.endsWith('/'))
    return 'Use the format owner/repo — e.g. facebook/react'
  return null
}

// ── Single input mode ─────────────────────────────────────────

export function SearchBar({ onSubmit, loading, placeholder = 'owner/repo — e.g. facebook/react' }) {
  const [value, setValue] = useState('')
  const [err,   setErr]   = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const msg = validateSlug(value)
    if (msg) { setErr(msg); return }
    setErr('')
    onSubmit(value.trim())
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <div className={`${styles.searchBox} ${err ? styles.hasError : ''}`}>
        <input
          className={styles.input}
          value={value}
          onChange={e => { setValue(e.target.value); setErr('') }}
          placeholder={placeholder}
          autoComplete="off"
          spellCheck="false"
          aria-label="Repository slug"
        />
        <button className={styles.btn} type="submit" disabled={loading}>
          {loading ? <span className={styles.spinner} /> : <>Analyse <span>→</span></>}
        </button>
      </div>
      {err && <p className={styles.error} role="alert">{err}</p>}
    </form>
  )
}

// ── Dual input mode (for Compare page) ───────────────────────

export function DualSearchBar({ onSubmit, loading }) {
  const [a, setA] = useState('')
  const [b, setB] = useState('')
  const [err, setErr] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const errA = validateSlug(a)
    const errB = validateSlug(b)
    if (errA || errB) { setErr(errA || errB); return }
    setErr('')
    onSubmit(a.trim(), b.trim())
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <div className={styles.dualBox}>
        <input
          className={styles.input}
          value={a}
          onChange={e => { setA(e.target.value); setErr('') }}
          placeholder="Repo A — e.g. facebook/react"
          autoComplete="off"
          spellCheck="false"
          aria-label="Repository A"
        />
        <span className={styles.vs}>VS</span>
        <input
          className={styles.input}
          value={b}
          onChange={e => { setB(e.target.value); setErr('') }}
          placeholder="Repo B — e.g. vuejs/vue"
          autoComplete="off"
          spellCheck="false"
          aria-label="Repository B"
        />
        <button className={styles.btn} type="submit" disabled={loading}>
          {loading ? <span className={styles.spinner} /> : <>Compare <span>→</span></>}
        </button>
      </div>
      {err && <p className={styles.error} role="alert">{err}</p>}
    </form>
  )
}
