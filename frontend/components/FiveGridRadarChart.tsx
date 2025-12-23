import React from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

// Chart.js にレーダーチャート用のコンポーネントを登録
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

type NameAnalysis = {
  tenkaku?: number;    // 天格
  jinkaku?: number;    // 人格
  chikaku?: number;    // 地格
  gaikaku?: number;    // 外格
  soukaku?: number;    // 総格
  name?: string;      // 任意：名前（ラベル用）
};

type Props = {
  analysis?: NameAnalysis | null
  height?: number
}

export default function FiveGridRadarChart({ analysis, height = 300 }: Props) {
  if (!analysis) return null

  const data = {
    labels: ['天格', '人格', '地格', '外格', '総格'],
    datasets: [
      {
        label: '五格',
        data: [
          analysis.tenkaku || 0,
          analysis.jinkaku || 0,
          analysis.chikaku || 0,
          analysis.gaikaku || 0,
          analysis.soukaku || 0,
        ],
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        pointBackgroundColor: 'rgba(54, 162, 235, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
      },
    ],
  }

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false as const },
      tooltip: { enabled: true },
    },
    scales: {
      r: {
        // 五格の最大値は大吉：5、最小値は大凶：0 とする
        suggestedMin: 0,
        suggestedMax: 5,
        ticks: {
          stepSize: 1,
          showLabelBackdrop: false,
        },
        pointLabels: {
          font: {
            size: 14,
          },
          color: '#333',
        },
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
        angleLines: {
          color: 'rgba(0,0,0,0.2)',
        },
      },
    },
  }

  return (
    <div style={{ height }}>
      <h4 style={{ marginTop: 10 }} className="text-lg font-semibold">五格バランス</h4>
      <Radar data={data} options={options} />
    </div>
  )
}
