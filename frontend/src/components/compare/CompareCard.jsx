/**
 * Renders one repo's data in the compare view.
 * Highlighted metrics are the ones where this repo "wins".
 */

import { fmtNumber, fmtPercent, fmtDate, labelColor } from '../../utils/format'
import styles from './CompareCard.module.css'

export default function CompareCard({ repoData, winners, side, accentColor }) {
  const { repo, health, warnings } = repoData
  const color = labelColor(health.label)

  const metrics = [
    {
      key:   'health_score',
      label: 'Health Score',
      value: health.health_score,
    },
    {
      key:   'commit_count_30d',
      label: 'Commits (30d)',
      value: fmtNumber(health.commit_count_30d),
    },
    {
      key:   'contributor_count',
      label: 'Contributors',
      value: fmtNumber(health.contributor_count),
    },
    {
      key:   'star_count',
      label: 'Stars',
      value: fmtNumber(health.star_count),
    },
    {
      key:   'pr_merge_rate',
      label: 'PR Merge Rate',
      value: health.pr_merge_rate != null ? fmtPercent(health.pr_merge_rate) : '—',
    },
    {
      key:   'open_issues',
      label: 'Open Issues',
      value: fmtNumber(health.open_issues),
    },
  ]

  return (
    <div className={`panel ${styles.card}`} style={{ '--accent': accentColor }}>
      {/* Accent border on top overriding default green */}
      <div className={styles.accentBar} style={{ background: accentColor }} />

      {/* Repo name + label */}
      <div className={styles.header}>
        <a
          className={styles.name}
          href={repo.html_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: accentColor }}
        >
          {repo.full_name}
        </a>
        <span className={`badge badge-${color}`}>{health.label}</span>
      </div>

      {repo.description && (
        <p className={styles.desc}>{repo.description}</p>
      )}

      {/* Score big display */}
      <div className={styles.scoreBig}>
        <span className={`${styles.scoreNum} ${styles[`score-${color}`]}`}>
          {health.health_score}
        </span>
        <span className={styles.scoreLabel}>/ 100</span>
      </div>

      {/* Dimension pills */}
      <div className={styles.dims}>
        {Object.entries(health.metrics).map(([k, v]) => (
          <div key={k} className={styles.dim}>
            <span className={styles.dimLabel}>{k}</span>
            <span className={styles.dimVal}>{v}</span>
          </div>
        ))}
      </div>

      {/* Metric grid */}
      <div className={styles.metricGrid}>
        {metrics.map(m => {
          const isWinner = winners[m.key] === side
          return (
            <div key={m.key} className={`${styles.metric} ${isWinner ? styles.winner : ''}`}>
              <span className={styles.metricLabel}>{m.label}</span>
              <span className={styles.metricValue}>{m.value}</span>
              {isWinner && <span className={styles.winBadge}>↑ leads</span>}
            </div>
          )
        })}
      </div>

      {/* Warnings summary */}
      {warnings?.length > 0 && (
        <div className={styles.warnSummary}>
          <span className={styles.warnIcon}>⚠</span>
          {warnings.length} warning{warnings.length !== 1 ? 's' : ''} detected
        </div>
      )}
    </div>
  )
}
