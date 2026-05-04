/**
 * Batch analysis — user enters up to 10 repos, gets a ranked table.
 */

import { useState } from 'react'
import { batchAnalyse }                 from '../utils/api'
import { ErrorMessage, LoadingSpinner } from '../components/common/Feedback'
import BatchResultsTable                from '../components/batch/BatchResultsTable'
import styles                           from './Page.module.css'
import bStyles                          from './BatchPage.module.css'

const PLACEHOLDER = `facebook/react\nvuejs/vue\nsveltejs/svelte\nangular/angular`
const MAX = 10

export default function BatchPage() {
  const [text,    setText]    = useState('')
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  function parseRepos() {
    return text
      .split('\n')
      .map(l => l.trim())
      .filter(Boolean)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const repos = parseRepos()

    if (repos.length === 0) { setError('Enter at least one repository.'); return }
    if (repos.length > MAX)  { setError(`Maximum ${MAX} repositories per batch.`); return }

    setLoading(true)
    setError(null)
    setData(null)

    try {
      const json = await batchAnalyse(repos)
      setData(json.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const count = parseRepos().length

  return (
    <div className={styles.page}>
      {/* Hero */}
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>
          Batch <em className={styles.heroEm}>rank repos</em>
        </h1>
        <p className={styles.heroSub}>
          Enter up to {MAX} repositories — one per line — and get them ranked by health score
        </p>

        <form className={bStyles.form} onSubmit={handleSubmit}>
          <div className={bStyles.textareaWrap}>
            <textarea
              className={bStyles.textarea}
              value={text}
              onChange={e => { setText(e.target.value); setError(null) }}
              placeholder={PLACEHOLDER}
              rows={6}
              spellCheck="false"
              aria-label="Repository list"
            />
            <span className={`${bStyles.counter} ${count > MAX ? bStyles.overLimit : ''}`}>
              {count} / {MAX}
            </span>
          </div>

          <button
            className={`btn btn-primary ${bStyles.submitBtn}`}
            type="submit"
            disabled={loading || count === 0}
          >
            {loading
              ? <><span className={bStyles.spinner} /> Analysing…</>
              : <>Analyse & Rank →</>
            }
          </button>
        </form>

        <ErrorMessage message={error} />
      </div>

      {loading && <LoadingSpinner text={`Analysing ${parseRepos().length} repositories…`} />}

      {data && (
        <BatchResultsTable
          results={data.results}
          failed={data.failed}
        />
      )}
    </div>
  )
}
