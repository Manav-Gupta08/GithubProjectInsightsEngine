import { useState } from 'react'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import AnalysePage from './pages/AnalysePage'
import ComparePage from './pages/ComparePage'
import BatchPage from './pages/BatchPage'

// Tab definitions — add new pages here
const TABS = [
  { id: 'analyse', label: 'Analyse' },
  { id: 'compare', label: 'Compare' },
  { id: 'batch',   label: 'Batch Rank' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('analyse')

  return (
    <div className="app-shell">
      <Header tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="app-main">
        {activeTab === 'analyse' && <AnalysePage />}
        {activeTab === 'compare' && <ComparePage />}
        {activeTab === 'batch'   && <BatchPage />}
      </main>

      <Footer />
    </div>
  )
}
