import React from 'react'


type Meishiki = {
  year?: string
  month?: string
  day?: string
  hour?: string
}

type Props = {
  analysis?: Meishiki | null
  height?: number
}

export default function MeishikiCards({ analysis }: Props) {
  if (!analysis) return null

  return (
    <div>
        <h3 style={{ marginTop: 10 }} className="text-lg font-semibold">命式</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
            <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-slate-500">年柱</div>
            <div className="mt-1 text-sm font-semibold">{analysis.year ?? '—'}</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-slate-500">月柱</div>
            <div className="mt-1 text-sm font-semibold">{analysis.month ?? '—'}</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-slate-500">日柱</div>
            <div className="mt-1 text-sm font-semibold">{analysis.day ?? '—'}</div>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-slate-500">時柱</div>
            <div className="mt-1 text-sm font-semibold">{analysis.hour ?? '—'}</div>
            </div>
        </div>
    </div>
  )
}
