/**
 * Central API client. All components import from here — never fetch() directly.
 */

const BASE = import.meta.env.VITE_API_URL || '/api'

/**
 * Generic fetch wrapper. Throws an Error whose message is the API's
 * error.message string so components can display it directly.
 */
async function apiFetch(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  const json = await resp.json()

  if (!json.success) {
    const msg = json?.error?.message ?? `HTTP ${resp.status}`
    const err = new Error(msg)
    err.code = json?.error?.code ?? 'UNKNOWN'
    err.status = resp.status
    throw err
  }

  return json  // { success, data, meta }
}

// ── Repository analysis ───────────────────────────────────────

export async function getRepo(slug) {
  const [owner, repo] = slug.split('/')
  return apiFetch(`repos/${owner}/${repo}`)
}

export async function compareRepos(slug1, slug2) {
  const params = new URLSearchParams({ repo1: slug1, repo2: slug2 })
  return apiFetch(`repos/compare?${params}`)
}

export async function batchAnalyse(repoList) {
  return apiFetch('repos/batch', {
    method: 'POST',
    body: JSON.stringify({ repos: repoList }),
  })
}

export async function getAiInsights(slug) {
  const [owner, repo] = slug.split('/')
  return apiFetch(`repos/${owner}/${repo}/ai-insights`)
}

export async function clearCache(slug = null) {
  return apiFetch('/cache', {
    method: 'DELETE',
    body: JSON.stringify(slug ? { repo: slug } : {}),
  })
}
