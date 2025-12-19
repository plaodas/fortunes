import React, { useEffect, useState } from 'react'
import Modal from '../components/Modal'

type NameAnalysis = {
  tenkaku?: number
  jinkaku?: number
  chikaku?: number
  gaikaku?: number
  soukaku?: number
  summary?: string
}

type AnalysisResult = {
  year?: string
  month?: string
  day?: string
  hour?: string
  nameAnalysis?: NameAnalysis
}

type AnalysisOut = {
  id: number
  name: string
  birth_date: string
  birth_hour: number
  result: AnalysisResult
  created_at?: string | null
}

export default function Home(): JSX.Element {
  const [name, setName] = useState<string>('')
  const [date, setDate] = useState<string>('1990-01-01')
  const [hour, setHour] = useState<number>(12)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [history, setHistory] = useState<AnalysisOut[]>([])
  const [selected, setSelected] = useState<AnalysisOut | null>(null)

  useEffect(() => {
    fetchHistory()
  }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, birth_date: date, birth_hour: Number(hour) }),
    })
    const body = await res.json()
    setResult(body.result)
    fetchHistory()
  }

  async function fetchHistory() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyses`)
      if (res.ok) {
        const arr: AnalysisOut[] = await res.json()
        setHistory(arr)
      }
    } catch (e) {
      // ignore
    }
  }

  function FiveElementChart(analysis?: NameAnalysis | null) {
    if (!analysis) return null
    const vals = [analysis.tenkaku || 0, analysis.jinkaku || 0, analysis.chikaku || 0, analysis.gaikaku || 0, analysis.soukaku || 0]
    const labels = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']
    const max = Math.max(...vals, 1)
    return (
      <div style={{ display: 'flex', gap: 8, alignItems: 'end', height: 120 }}>
        {vals.map((v, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ width: 40, height: Math.round((v / max) * 100), background: '#4f46e5', margin: '0 auto' }} />
            <div style={{ fontSize: 12 }}>{labels[i]}</div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <main className="container">
      <div className="hero card">
        <h1 className="title">Fortunes</h1>
        <p className="muted" style={{ marginTop: 8 }}>四柱推命と姓名判断から本当のあなたを暴きます</p>
        <form onSubmit={submit} style={{ marginTop: 8 }}>
          <div className="form-grid">
            <div className="form-row">
              <label>Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="form-row">
              <label>Birth date</label>
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
            </div>
            <div className="form-row">
              <label>Birth hour</label>
              <input type="number" min={0} max={23} value={hour} onChange={(e) => setHour(Number(e.target.value))} required />
            </div>
            <div style={{ alignSelf: 'end' }}>
              <button className="btn" type="submit">Analyze</button>
            </div>
          </div>
        </form>
      </div>

      {result && (
        <section style={{ marginTop: 16 }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 className="text-2xl font-bold">Result</h2>
              <div className="muted">分析日時: {new Date().toLocaleString()}</div>
            </div>
            <div className="result-pre">{JSON.stringify(result, null, 2)}</div>
            <h3 style={{ marginTop: 10 }} className="text-lg font-semibold">五行バランス</h3>
            <div className="chart">
              {(() => {
                const analysis = result.nameAnalysis
                if (!analysis) return null
                const vals = [analysis.tenkaku || 0, analysis.jinkaku || 0, analysis.chikaku || 0, analysis.gaikaku || 0, analysis.soukaku || 0]
                const colors = ['#10b981', '#fb923c', '#f59e0b', '#60a5fa', '#a78bfa']
                const max = Math.max(...vals, 1)
                return vals.map((v, i) => (
                  <div key={i} className="bar" style={{ height: `${Math.round((v / max) * 100)}px`, background: colors[i] }} />
                ))
              })()}
            </div>
          </div>
        </section>
      )}

      {history.length > 0 && (
        <section style={{ marginTop: 16 }}>
          <h2>History</h2>
          <div className="history">
            {history.map((h) => (
              <button
                key={h.id}
                className="history-item text-left"
                onClick={() => setSelected(h)}
                aria-haspopup="dialog"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{h.name}</strong>
                    <div className="muted">{h.birth_date} · {h.birth_hour}時</div>
                  </div>
                  <div className="muted">#{h.id}</div>
                </div>
                <div className="summary">{h.result?.nameAnalysis?.summary}</div>
              </button>
            ))}
          </div>
        </section>
      )}

      {selected && (
        <Modal title={<>
          <div>{selected.name}</div>
          <div className="muted">{selected.birth_date} · {selected.birth_hour}時</div>
        </>} onClose={() => setSelected(null)}>
          <h4 className="font-semibold">五行バランス</h4>
          <div className="chart">
            {(() => {
              const analysis = selected.result?.nameAnalysis
              if (!analysis) return null
              const vals = [analysis.tenkaku || 0, analysis.jinkaku || 0, analysis.chikaku || 0, analysis.gaikaku || 0, analysis.soukaku || 0]
              const labels = ['木','火','土','金','水']
              const colors = ['#10b981', '#fb923c', '#f59e0b', '#60a5fa', '#a78bfa']
              const max = Math.max(...vals, 1)
              return vals.map((v,i) => (
                <div key={i} style={{ textAlign:'center' }}>
                  <div className="bar" style={{ height: `${Math.round((v/max)*100)}px`, background: colors[i], margin:'0 auto' }} />
                  <div className="muted mt-2">{labels[i]}</div>
                </div>
              ))
            })()}
          </div>
          <div style={{ marginTop: 16 }}>
            <h4 className="font-semibold">詳細 JSON</h4>
            <pre className="result-pre">{JSON.stringify(selected.result, null, 2)}</pre>
          </div>
        </Modal>
      )}
    </main>
  )
}
