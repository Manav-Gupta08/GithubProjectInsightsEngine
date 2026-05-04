import styles from './Header.module.css'

export default function Header({ tabs, activeTab, onTabChange }) {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>

        <div className={styles.logo}>
          <span className={styles.logoHex} aria-hidden="true">⬡</span>
          <span className={styles.logoText}>INSIGHTS ENGINE</span>
        </div>

        <nav className={styles.nav} aria-label="Main navigation">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`${styles.navBtn} ${activeTab === tab.id ? styles.active : ''}`}
              onClick={() => onTabChange(tab.id)}
              aria-current={activeTab === tab.id ? 'page' : undefined}
            >
              {tab.label}
            </button>
          ))}
        </nav>

      </div>
    </header>
  )
}
