/**
 * Full single-repo analysis dashboard.
 * Receives the shaped API response and delegates to child panels.
 */

import RepoMetaBar        from './RepoMetaBar'
import ScoreCard          from './ScoreCard'
import CommitChart        from './CommitChart'
import ContributorList    from './ContributorList'
import WarningList        from './WarningList'
import RecommendationCard from './RecommendationCard'
import styles             from './Dashboard.module.css'

export default function Dashboard({ data }) {
  const { repo, health, contributors, warnings, recommendation } = data

  // Build the slug so RecommendationCard can call AI insights
  const slug = repo.full_name

  return (
    <div className={`${styles.dashboard} animate-fade-up`}>
      <RepoMetaBar repo={repo} health={health} />

      <div className={styles.grid}>
        {/* Left column */}
        <div className={styles.colLeft}>
          <ScoreCard health={health} />
        </div>

        {/* Right column */}
        <div className={styles.colRight}>
          <CommitChart
            trend={health.commit_trend}
            weeklyAvg={health.weekly_avg_commits}
          />
          <ContributorList contributors={contributors} />
        </div>
      </div>

      {/* Full-width bottom rows */}
      <WarningList warnings={warnings} />
      <RecommendationCard recommendation={recommendation} repoSlug={slug} />
    </div>
  )
}
