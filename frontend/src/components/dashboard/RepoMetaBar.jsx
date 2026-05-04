/**
 * Top section of the dashboard: repo title, language badge,
 * archived warning, description, and KPI strip.
 */

import { fmtNumber, fmtPercent } from '../../utils/format'
import styles from './RepoMetaBar.module.css'

const KPI_ITEMS = [
  { key: 'stars',       label: 'Stars',         fmt: fmtNumber },
  { key: 'forks',       label: 'Forks',         fmt: fmtNumber },
  { key: 'open_issues', label: 'Open Issues',    fmt: fmtNumber },
]

export default function RepoMetaBar({ repo, health }) {
  const dynamicKpis = [
    ...KPI_ITEMS.map(k => ({ label: k.label, value: k.fmt(repo[k.key]) })),
    { label: 'Commits (30d)', value: fmtNumber(health.commit_count_30d) },
    { label: 'Contributors',  value: fmtNumber(health.contributor_count) },
    { label: 'PR Merge Rate', value: health.pr_merge_rate != null ? fmtPercent(health.pr_merge_rate) : '—' },
  ]

  return (
    <div className={styles.wrap}>
      {/* Title row */}
      <div className={styles.titleRow}>
        <div className={styles.titleLeft}>
          <a
            className={styles.repoName}
            href={repo.html_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {repo.full_name}
          </a>
          {repo.language && (
            <span className="badge badge-blue">{repo.language}</span>
          )}
          {repo.archived && (
            <span className="badge badge-red">ARCHIVED</span>
          )}
          {repo.license && repo.license !== 'None' && (
            <span className="badge badge-muted">{repo.license}</span>
          )}
        </div>
      </div>

      {/* Description */}
      {repo.description && (
        <p className={styles.desc}>{repo.description}</p>
      )}

      {/* Topics */}
      {repo.topics?.length > 0 && (
        <div className={styles.topics}>
          {repo.topics.map(t => (
            <span key={t} className={styles.topic}>{t}</span>
          ))}
        </div>
      )}

      {/* KPI strip */}
      <div className={styles.kpiStrip}>
        {dynamicKpis.map(kpi => (
          <div key={kpi.label} className={styles.kpiCard}>
            <span className={styles.kpiLabel}>{kpi.label}</span>
            <span className={styles.kpiValue}>{kpi.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
