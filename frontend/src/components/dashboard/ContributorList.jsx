/**
 * Ranked list of top contributors with avatar, bar, and commit count.
 */

import { fmtNumber } from '../../utils/format'
import styles from './ContributorList.module.css'

export default function ContributorList({ contributors }) {
  if (!contributors?.length) {
    return (
      <div className="panel">
        <p className="panel-title">Top Contributors</p>
        <p className={styles.empty}>No contributor data available.</p>
      </div>
    )
  }

  const max = contributors[0].contributions || 1

  return (
    <div className="panel">
      <p className="panel-title">Top Contributors</p>
      <ul className={styles.list}>
        {contributors.map((c, i) => (
          <li key={c.login} className={styles.item} style={{ animationDelay: `${i * 50}ms` }}>
            <span className={styles.rank}>#{i + 1}</span>

            <img
              className={styles.avatar}
              src={c.avatar_url}
              alt={c.login}
              loading="lazy"
              width={34}
              height={34}
            />

            <div className={styles.info}>
              <a
                className={styles.login}
                href={c.html_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {c.login}
              </a>
              <div className={styles.barBg}>
                <div
                  className={styles.barFill}
                  style={{ '--w': `${(c.contributions / max) * 100}%` }}
                />
              </div>
            </div>

            <span className={styles.count}>{fmtNumber(c.contributions)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
