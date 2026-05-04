/* ── ErrorMessage.jsx ── */
import styles from './Feedback.module.css'

export function ErrorMessage({ message }) {
  if (!message) return null
  return (
    <div className={styles.error} role="alert">
      <span className={styles.errorIcon}>⚠</span>
      {message}
    </div>
  )
}

/* ── LoadingSpinner.jsx ── */
export function LoadingSpinner({ text = 'Fetching repository data…' }) {
  return (
    <div className={styles.spinnerWrap} aria-live="polite">
      <div className={styles.ring} />
      <p className={styles.spinnerText}>{text}</p>
    </div>
  )
}
