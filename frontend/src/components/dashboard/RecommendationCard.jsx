/**
 * "Should I use this?" panel — shows the plain-language recommendation
 * and an optional AI insight if the feature is enabled.
 */

import { useState } from 'react'
import { getAiInsights } from '../../utils/api'
import styles from './RecommendationCard.module.css'

export default function RecommendationCard({ recommendation, repoSlug }) {
  const [insight,    setInsight]    = useState(null)
  const [aiLoading,  setAiLoading]  = useState(false)
  const [aiError,    setAiError]    = useState(null)
  const [aiDisabled, setAiDisabled] = useState(false)

  async function fetchInsight() {
    setAiLoading(true)
    setAiError(null)
    try {
      const json = await getAiInsights(repoSlug)
      setInsight(json.data.insight)
    } catch (err) {
      if (err.status === 503) {
        setAiDisabled(true)
        setAiError('AI insights are not enabled on this server. Set AI_INSIGHTS_ENABLED=true in .env.')
      } else {
        setAiError(err.message)
      }
    } finally {
      setAiLoading(false)
    }
  }

  return (
    <div className="panel">
      <p className="panel-title">Should You Use This?</p>

      <p className={styles.rec}>{recommendation}</p>

      {/* AI insights section */}
      {!insight && !aiDisabled && (
        <button
          className={styles.aiBtn}
          onClick={fetchInsight}
          disabled={aiLoading}
        >
          {aiLoading
            ? <><span className={styles.spinner} /> Generating insight…</>
            : <><span>✦</span> Generate AI Insight</>
          }
        </button>
      )}

      {aiError && (
        <p className={styles.aiError}>{aiError}</p>
      )}

      {insight && (
        <div className={styles.aiInsight}>
          <span className={styles.aiLabel}>✦ AI Insight</span>
          <p className={styles.aiText}>{insight}</p>
        </div>
      )}
    </div>
  )
}
