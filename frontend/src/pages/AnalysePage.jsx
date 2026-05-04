/**
 * Single-repository analysis page.
 */

import useRepo from '../hooks/useRepo'
import { SearchBar }           from '../components/common/SearchBar'
import { ErrorMessage, LoadingSpinner } from '../components/common/Feedback'
import Dashboard               from '../components/dashboard/Dashboard'
import styles                  from './Page.module.css'

export default function AnalysePage() {
  const { data, loading, error, analyse } = useRepo()

  return (
    <div className={styles.page}>
      {/* Hero / search */}
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>
          Decode any <em className={styles.heroEm}>GitHub repository</em>
        </h1>
        <p className={styles.heroSub}>
          Commit trends · Contributor health · Activity score · Red flags
        </p>
        <SearchBar onSubmit={analyse} loading={loading} />
        <ErrorMessage message={error} />
      </div>

      {/* Results */}
      {loading && <LoadingSpinner />}
      {data    && <Dashboard data={data} />}
    </div>
  )
}
