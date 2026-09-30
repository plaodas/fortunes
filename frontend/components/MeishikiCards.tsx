import React from 'react'
import { currentDaiunIndex } from '../lib/readingDisplay'


type PillarDetail = {
  tsuhen?: string
  juniun?: string
}

type DaiunRow = {
  start: string
  kanshi: string
  tsuhen: string
}

type Meishiki = {
  year?: string
  month?: string
  day?: string
  hour?: string
  strength?: string
  pillars?: {
    year?: PillarDetail
    month?: PillarDetail
    day?: PillarDetail
    hour?: PillarDetail
  }
  daiun?: DaiunRow[]
}

type Props = {
  analysis?: Meishiki | null
  birthDate?: string
  height?: number
}

const PILLARS: { key: 'year' | 'month' | 'day' | 'hour'; label: string }[] = [
  { key: 'year', label: '年柱' },
  { key: 'month', label: '月柱' },
  { key: 'day', label: '日柱' },
  { key: 'hour', label: '時柱' },
]

export default function MeishikiCards({ analysis, birthDate }: Props) {
  if (!analysis) return null
  const current = birthDate && analysis.daiun ? currentDaiunIndex(analysis.daiun, birthDate) : -1

  return (
    <div>
        <h3 style={{ marginTop: 10 }} className="text-lg font-semibold">命式</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
            {PILLARS.map(({ key, label }) => {
              const detail = analysis.pillars?.[key]
              return (
                <div key={key} className="p-3 bg-gray-50 rounded-lg">
                  <div className="text-xs text-slate-500">{label}</div>
                  <div className="mt-1 text-sm font-semibold">{analysis[key] ?? '—'}</div>
                  {detail?.tsuhen && <div className="mt-1 text-xs text-slate-600">通変星 {detail.tsuhen}</div>}
                  {detail?.juniun && <div className="text-xs text-slate-600">十二運 {detail.juniun}</div>}
                </div>
              )
            })}
        </div>
        {analysis.strength && <p className="mt-3 text-sm">身強身弱：{analysis.strength}</p>}
        {analysis.daiun && analysis.daiun.length > 0 && (
          <div className="mt-3">
            <h4 className="text-sm font-semibold">大運</h4>
            <ul className="mt-1 text-sm text-slate-700">
              {analysis.daiun.map((row, index) => (
                <li key={row.start} className={index === current ? 'daiun-current' : undefined}>
                  {row.start} {row.kanshi}（{row.tsuhen}）{index === current ? ' いま' : ''}
                </li>
              ))}
            </ul>
          </div>
        )}
    </div>
  )
}
