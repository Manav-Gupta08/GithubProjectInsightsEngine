/**
 * 30-day commit trend line chart.
 * Uses react-chartjs-2 which wraps Chart.js declaratively.
 */

import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement,
  LineElement, Filler, Tooltip,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import styles from './CommitChart.module.css'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip)

// Shorten date labels: "2024-05-01" → "01 May"
function shortLabel(iso) {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

export default function CommitChart({ trend, color = '#00e5a0', weeklyAvg }) {
  const labels = trend.labels.map(shortLabel)
  const counts = trend.counts

  const data = {
    labels,
    datasets: [{
      data: counts,
      borderColor:     color,
      backgroundColor: hexToRgba(color, 0.07),
      pointBackgroundColor: color,
      pointRadius:     3,
      pointHoverRadius: 5,
      borderWidth: 2,
      fill: true,
      tension: 0.35,
    }],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 700 },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#12131a',
        borderColor:     '#252638',
        borderWidth: 1,
        titleColor:  '#6b6b9a',
        bodyColor:   '#e4e4f0',
        titleFont:   { family: "'Space Mono'" },
        bodyFont:    { family: "'Space Mono'" },
        callbacks: {
          title: items => items[0].label,
          label: item => ` ${item.raw} commit${item.raw !== 1 ? 's' : ''}`,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#3d3d5c',
          font: { family: "'Space Mono'", size: 10 },
          // Show every 5th label to avoid crowding
          callback: (_, idx) => idx % 5 === 0 ? labels[idx] : '',
          maxRotation: 0,
        },
        grid: { color: '#181924' },
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: '#3d3d5c',
          font: { family: "'Space Mono'", size: 10 },
          stepSize: 1,
        },
        grid: { color: '#181924' },
      },
    },
  }

  return (
    <div className={`panel ${styles.chartPanel}`}>
      <div className={styles.header}>
        <p className="panel-title" style={{ margin: 0 }}>
          Commit Activity <span className={styles.sub}>— last 30 days</span>
        </p>
        {weeklyAvg !== undefined && (
          <span className={styles.stat}>
            Weekly avg: <strong>{weeklyAvg}</strong>
          </span>
        )}
      </div>
      <div className={styles.chartWrap}>
        <Line data={data} options={options} />
      </div>
    </div>
  )
}

function hexToRgba(hex, alpha) {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}
