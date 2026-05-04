/**
 * Ranked table of repos from batch analysis.
 * Each row shows rank, name, score, label, and key metrics.
 */

import { fmtNumber, fmtPercent, labelColor } from '../../utils/format'
import styles from './BatchResultsTable.module.css'

export default function BatchResultsTable({ results, failed }) {
  return (
    <div className={styles.wrap}>
      {/* Main results table */}
      <div className="panel">
        <p className="panel-title">
          Ranked Results
          <span className={styles.countBadge}>{results.length}</span>
        </p>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>#</th>
                <th>Repository</th>
                <th>Score</th>
                <th>Status</th>
                <th>Stars</th>
                <th>Commits (30d)</th>
                <th>Contributors</th>
                <th>Warnings</th>
              </tr>
            </thead>
            <tbody>
              {results.map(r => {
                const color = labelColor(r.label)
                return (
                  <tr key={r.slug} className={styles.row}>
                    <td className={styles.rankCell}>
                      {r.rank === 1 && <span className={styles.crown}>🥇</span>}
                      {r.rank === 2 && <span className={styles.crown}>🥈</span>}
                      {r.rank === 3 && <span className={styles.crown}>🥉</span>}
                      {r.rank > 3   && <span className={styles.rankNum}>#{r.rank}</span>}
                    </td>
                    <td>
                      <a
                        className={styles.repoLink}
                        href={r.html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {r.full_name}
                      </a>
                      {r.language && (
                        <span className={styles.lang}>{r.language}</span>
                      )}
                    </td>
                    <td>
                      <span className={`${styles.score} ${styles[`score-${color}`]}`}>
                        {r.health_score}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${color}`}>{r.label}</span>
                    </td>
                    <td className={styles.num}>{fmtNumber(r.stars)}</td>
                    <td className={styles.num}>{fmtNumber(r.metrics?.commit_count_30d ?? r.health_score)}</td>
                    <td className={styles.num}>{fmtNumber(r.metrics?.contributor_count)}</td>
                    <td>
                      {r.warning_count > 0
                        ? <span className={styles.warnCount}>⚠ {r.warning_count}</span>
                        : <span className={styles.noWarn}>✓</span>
                      }
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Failed repos */}
      {failed?.length > 0 && (
        <div className={`panel ${styles.failedPanel}`}>
          <p className="panel-title">Failed to Analyse</p>
          <ul className={styles.failedList}>
            {failed.map(f => (
              <li key={f.slug} className={styles.failedItem}>
                <span className={styles.failedSlug}>{f.slug}</span>
                <span className={styles.failedReason}>{f.reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
