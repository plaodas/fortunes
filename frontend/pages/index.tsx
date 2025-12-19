import React, { useEffect, useState } from 'react'

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
      <div className="card">
        <h1>Fortunes - MVP</h1>
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
            <h2>Result</h2>
            <div className="result-pre">{JSON.stringify(result, null, 2)}</div>
            <h3 style={{ marginTop: 10 }}>五行バランス</h3>
            <div className="chart">
              {(() => {
                const analysis = result.nameAnalysis
                if (!analysis) return null
                const vals = [analysis.tenkaku || 0, analysis.jinkaku || 0, analysis.chikaku || 0, analysis.gaikaku || 0, analysis.soukaku || 0]
                const max = Math.max(...vals, 1)
                return vals.map((v, i) => (
                  <div key={i} className="bar" style={{ height: `${Math.round((v / max) * 100)}px` }} />
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
              <div key={h.id} className="history-item">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{h.name}</strong>
                    <div className="muted">{h.birth_date} · {h.birth_hour}時</div>
                  </div>
                  <div className="muted">#{h.id}</div>
                </div>
                <div className="summary">{h.result?.nameAnalysis?.summary}</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}
