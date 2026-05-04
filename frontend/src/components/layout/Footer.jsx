import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <span>GitHub Insights Engine · Data via GitHub REST API · Cache TTL 5 min</span>
    </footer>
  )
}
