/**
 * Displays the circular health score ring, dimension breakdown bars,
 * and last-commit date.
 */

import { useEffect, useRef } from 'react'
import { fmtDate, labelColor } from '../../utils/format'
import styles from './ScoreCard.module.css'

const CIRCUMFERENCE = 2 * Math.PI * 54  // r=54 in SVG

const DIMENSION_LABELS = {
  activity:    'Activity',
  community:   'Community',
  maintenance: 'Maintenance',
}

export default function ScoreCard({ health }) {
  const ringRef   = useRef(null)
  const numberRef = useRef(null)

  const score  = health.health_score
  const label  = health.label
  const color  = labelColor(label)

  // Animate ring fill on mount/score change
  useEffect(() => {
    if (!ringRef.current) return
    const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE
    ringRef.current.style.strokeDashoffset = offset
  }, [score])

  // Animate score counter
  useEffect(() => {
    const el = numberRef.current
    if (!el) return
    let start = null
    const duration = 900

    function step(ts) {
      if (!start) start = ts
      const progress = Math.min((ts - start) / duration, 1)
      const eased    = 1 - Math.pow(1 - progress, 3)
      el.textContent = Math.round(eased * score)
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [score])

  return (
    <div className={`panel ${styles.card}`}>
      <p className="panel-title">Health Score</p>

      {/* SVG ring */}
      <div className={styles.ringWrap}>
        <svg className={styles.ring} viewBox="0 0 120 120">
          <circle className={styles.ringBg}   cx="60" cy="60" r="54" />
          <circle
            ref={ringRef}
            className={`${styles.ringFill} ${styles[`ring-${color}`]}`}
            cx="60" cy="60" r="54"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={CIRCUMFERENCE}
          />
        </svg>
        <div className={styles.ringInner}>
          <span ref={numberRef} className={styles.scoreNum}>0</span>
          <span className={`${styles.scoreLabel} ${styles[`label-${color}`]}`}>
            {label.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Dimension bars */}
      <div className={styles.dimensions}>
        {Object.entries(health.metrics).map(([key, val]) => (
          <DimensionBar key={key} label={DIMENSION_LABELS[key] || key} value={val} />
        ))}
      </div>

      {/* Last commit */}
      <div className={styles.lastCommit}>
        <span className={styles.lcLabel}>Last commit</span>
        <span className={styles.lcValue}>
          {health.last_commit_date ? fmtDate(health.last_commit_date) : 'No commits found'}
        </span>
      </div>
    </div>
  )
}

function DimensionBar({ label, value }) {
  return (
    <div className={styles.dimRow}>
      <div className={styles.dimMeta}>
        <span className={styles.dimLabel}>{label}</span>
        <span className={styles.dimValue}>{value}</span>
      </div>
      <div className={styles.barBg}>
        <div
          className={styles.barFill}
          style={{ '--target-width': `${value}%` }}
        />
      </div>
    </div>
  )
}
