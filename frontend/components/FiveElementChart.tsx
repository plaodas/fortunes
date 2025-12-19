import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

type NameAnalysis = {
  tenkaku?: number
  jinkaku?: number
  chikaku?: number
  gaikaku?: number
  soukaku?: number
  summary?: string
}

type Props = {
  analysis?: NameAnalysis | null
  height?: number
}

export default function FiveElementChart({ analysis, height = 140 }: Props) {
  if (!analysis) return null

  const labels = ['木', '火', '土', '金', '水']
  const vals = [analysis.tenkaku || 0, analysis.jinkaku || 0, analysis.chikaku || 0, analysis.gaikaku || 0, analysis.soukaku || 0]
  const colors = ['#10b981', '#fb923c', '#f59e0b', '#60a5fa', '#a78bfa']

  const data = {
    labels,
    datasets: [
      {
        label: '五行',
        data: vals,
        backgroundColor: colors,
        borderRadius: 6,
        barThickness: 28,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { grid: { display: false }, ticks: { color: '#475569' } },
      y: { beginAtZero: true, grid: { color: '#eef2ff' }, ticks: { color: '#475569' } },
    },
    plugins: {
      legend: { display: false as const },
      tooltip: { enabled: true },
    },
  }

  return (
    <div style={{ height }}>
      <Bar data={data} options={options as any} />
    </div>
  )
}
