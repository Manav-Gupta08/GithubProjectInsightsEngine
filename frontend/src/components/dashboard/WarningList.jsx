/**
 * Displays red-flag warnings returned by the backend detector.
 * Shows nothing when there are no warnings (clean repos stay clean-looking).
 */

import { severityColor } from '../../utils/format'
import styles from './WarningList.module.css'

const SEVERITY_ICON = { high: '🔴', medium: '🟡', low: '🔵' }

export default function WarningList({ warnings }) {
  if (!warnings?.length) return null

  return (
    <div className="panel">
      <p className="panel-title">
        Red Flags
        <span className={styles.count}>{warnings.length}</span>
      </p>
      <ul className={styles.list}>
        {warnings.map((w, i) => (
          <li
            key={w.code}
            className={`${styles.item} ${styles[severityColor(w.severity)]}`}
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <span className={styles.icon} aria-hidden="true">
              {SEVERITY_ICON[w.severity] ?? '⚪'}
            </span>
            <span className={styles.message}>{w.message}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
