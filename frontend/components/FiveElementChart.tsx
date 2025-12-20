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

type BirthAnalysis = {
  wood?: number
  fire?: number
  earth?: number
  metal?: number
  water?: number
  summary?: string
}

type Props = {
  analysis?: BirthAnalysis | null
  height?: number
}

export default function FiveElementChart({ analysis, height = 200 }: Props) {
  // analysis は { wood: 3, fire: 2, earth: 1, metal: 2, water: 0 } のようなオブジェクト
  if (!analysis) return null

  const labels = ['木', '火', '土', '金', '水']
  const vals = [analysis.wood || 0, analysis.fire || 0, analysis.earth || 0, analysis.metal || 0, analysis.water || 0]
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
      y: { beginAtZero: true, grid: { color: '#eef2ff' }, ticks: { stepSize: 1, color: '#475569' } },
    },
    plugins: {
      legend: { display: false as const },
      tooltip: { enabled: true },
    },
  }

  return (
    <div style={{ height }}>
      <h4 style={{ marginTop: 10 }} className="text-lg font-semibold">五行バランス</h4>
      <Bar data={data} options={options as any} />
    </div>
  )
}
