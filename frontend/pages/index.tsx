import React, { useEffect, useState } from 'react'
import Modal from '../components/Modal'
import FiveElementChart from '../components/FiveElementChart'

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

  // FiveElementChart component moved to components/FiveElementChart.tsx

  return (
    <main className="container">
      <div className="hero card">
        <h1 className="title">Fortunes</h1>
        <p className="muted" style={{ marginTop: 8 }}>四柱推命と姓名判断から本当のあなたを暴きます</p>
        <form onSubmit={submit} style={{ marginTop: 8 }}>
          <div className="form-grid">
            <div className="form-row">
              <label>名前</label>
              <input type="text" className="input" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="form-row">
              <label>生年月日</label>
              <input type="date" className="input" value={date} onChange={(e) => setDate(e.target.value)} required />
            </div>
            <div className="form-row">
              <label>出生時間</label>
              <input type="number" className="input" min={0} max={23} value={hour} onChange={(e) => setHour(Number(e.target.value))} required />
            </div>
            <div style={{ alignSelf: 'end' }}>
              <button className="btn" type="submit">分析する</button>
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
              <FiveElementChart analysis={result.nameAnalysis} />
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
            <FiveElementChart analysis={selected.result?.nameAnalysis} />
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
