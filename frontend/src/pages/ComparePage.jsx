/**
 * Side-by-side comparison of two repositories.
 */

import { useState } from 'react'
import { compareRepos }                 from '../utils/api'
import { DualSearchBar }                from '../components/common/SearchBar'
import { ErrorMessage, LoadingSpinner } from '../components/common/Feedback'
import CompareCard                      from '../components/compare/CompareCard'
import CommitChart                      from '../components/dashboard/CommitChart'
import styles                           from './Page.module.css'
import cStyles                          from './ComparePage.module.css'

export default function ComparePage() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  async function handleCompare(slugA, slugB) {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const json = await compareRepos(slugA, slugB)
      setData(json.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      {/* Hero / search */}
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>
          Compare <em className={styles.heroEm}>repositories</em>
        </h1>
        <p className={styles.heroSub}>
          Head-to-head health analysis across activity, community, and maintenance
        </p>
        <DualSearchBar onSubmit={handleCompare} loading={loading} />
        <ErrorMessage message={error} />
      </div>

      {loading && <LoadingSpinner text="Fetching both repositories…" />}

      {data && (
        <div className={`${cStyles.results} animate-fade-up`}>
          {/* Summary bar */}
          <div className={cStyles.summaryBar}>
            <span className={cStyles.summaryText}>{data.comparison.summary}</span>
          </div>

          {/* Card grid */}
          <div className={cStyles.cardGrid}>
            <CompareCard
              repoData={data.repo_1}
              winners={data.comparison.winners}
              side="repo_1"
              accentColor="var(--accent-a)"
            />
            <CompareCard
              repoData={data.repo_2}
              winners={data.comparison.winners}
              side="repo_2"
              accentColor="var(--accent-b)"
            />
          </div>

          {/* Commit trend charts */}
          <div className={cStyles.chartRow}>
            <CommitChart
              trend={data.repo_1.health.commit_trend}
              color="#00e5a0"
              weeklyAvg={data.repo_1.health.weekly_avg_commits}
            />
            <CommitChart
              trend={data.repo_2.health.commit_trend}
              color="#f5a623"
              weeklyAvg={data.repo_2.health.weekly_avg_commits}
            />
          </div>
        </div>
      )}
    </div>
  )
}
