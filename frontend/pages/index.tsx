import React, { useEffect, useState } from 'react'
import Modal from '../components/Modal'
import FiveElementChart from '../components/FiveElementChart'
import FiveGridRadarChart from '../components/FiveGridRadarChart'
import MeishikiCards from '../components/MeishikiCards'

type Meishiki = {
  year?: string
  month?: string
  day?: string
  hour?: string
}

type Gogyo = {
  wood?: number
  fire?: number
  earth?: number
  metal?: number
  water?: number
}

type BirthAnalysis = {
  meisiki: Meishiki
  gogyo: Gogyo
  summary?: string
}

type NameAnalysis = {
  tenkaku?: number
  jinkaku?: number
  chikaku?: number
  gaikaku?: number
  soukaku?: number
  summary?: string
}

type AnalysisResult = {
  birth_analysis?: BirthAnalysis
  name_analysis?: NameAnalysis
  summary?: string
}

type AnalysisOut = {
  id: number
  name: string
  birth_date: string
  birth_hour: number
  result_birth: BirthAnalysis
  result_name: NameAnalysis
  summary: string
  created_at: string
}

export default function Home(): JSX.Element {
  const [name, setName] = useState<string>('')
  const [date, setDate] = useState<string>('1990-01-01')
  const [hour, setHour] = useState<number>(12)
  const [nameError, setNameError] = useState<string | null>(null)
  const [dateError, setDateError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [history, setHistory] = useState<AnalysisOut[]>([])
  const [selected, setSelected] = useState<AnalysisOut | null>(null)

  const isFormValid = !nameError && !dateError && name.trim().length > 0

  useEffect(() => {
    fetchHistory()
  }, [])
  function runValidation() {
    // name: at least 2 characters
    if (name.trim().length === 0) {
      setNameError('名前を入力してください')
    } else if (name.trim().length < 2) {
      setNameError('名前は2文字以上で入力してください')
    } else {
      setNameError(null)
    }

    // date: valid format and not in the future
    const parsed = Date.parse(date)
    if (isNaN(parsed)) {
      setDateError('有効な日付を選択してください')
    } else if (parsed > Date.now()) {
      setDateError('未来の日付は指定できません')
    } else {
      setDateError(null)
    }
  }

  useEffect(() => {
    runValidation()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name, date])

  async function submit(e: React.FormEvent) {
    e.preventDefault()

    // synchronous local validation to decide whether to submit
    const nameValid = name.trim().length >= 2
    const parsed = Date.parse(date)
    const dateValid = !isNaN(parsed) && parsed <= Date.now()

    if (!nameValid || !dateValid) {
      // set errors for user feedback
      runValidation()
      return
    }

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
        <p className="muted" style={{ marginTop: 8 }}>四柱推命と姓名判断から生来の運命を読み解くアプリ</p>
        <form onSubmit={submit} style={{ marginTop: 8 }}>
          <div className="form-grid">
            <div className="form-row">
              <label htmlFor="name">名前</label>
              <input
                id="name"
                type="text"
                className={`input ${nameError ? 'invalid' : ''}`}
                value={name}
                onChange={(e) => setName(e.target.value)}
                aria-invalid={!!nameError}
                aria-describedby={nameError ? 'name-error' : undefined}
                required
              />
              {nameError && <div id="name-error" className="error-text">{nameError}</div>}
            </div>
            <div className="form-row">
              <label htmlFor="birth-date">生年月日</label>
              <input
                id="birth-date"
                type="date"
                className={`input ${dateError ? 'invalid' : ''}`}
                value={date}
                onChange={(e) => setDate(e.target.value)}
                aria-invalid={!!dateError}
                aria-describedby={dateError ? 'date-error' : undefined}
                required
              />
              {dateError && <div id="date-error" className="error-text">{dateError}</div>}
            </div>
            <div className="form-row">
              <label htmlFor="birth-hour">生まれた時間</label>
              <select
                id="birth-hour"
                className="input"
                value={String(hour)}
                onChange={(e) => setHour(Number(e.target.value))}
                required
              >
                {Array.from({ length: 24 }).map((_, i) => (
                  <option key={i} value={String(i)}>{i}時</option>
                ))}
              </select>
            </div>
            <div className="form-action" style={{ alignSelf: 'end' }}>
              <button className="btn" type="submit" disabled={!isFormValid}>鑑定する</button>
            </div>
          </div>
        </form>
      </div>

      {result && (
        <section style={{ marginTop: 16 }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 className="text-2xl font-bold">鑑定結果</h2>
            </div>
            <div className="meishiki-cards">
              <MeishikiCards analysis={result.birth_analysis?.meisiki} />
            </div>
            <div className="chart">
              <FiveElementChart analysis={result.birth_analysis?.gogyo} />
            </div>
            <div className="chart">
              <FiveGridRadarChart analysis={result.name_analysis} />
            </div>
            {/* <div className="result-pre">{JSON.stringify(result, null, 2)}</div> */}
          </div>
        </section>
      )}

      {history.length > 0 && (
        <section style={{ marginTop: 16 }}>
          <h2>過去の鑑定</h2>
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
                    <div className="muted">{h.birth_date} · {h.birth_hour}時生まれ</div>
                  </div>
                  <div className="muted">#{h.id}</div>
                </div>
                <div className="summary">{h.summary}</div>
              </button>
            ))}
          </div>
        </section>
      )}

      {selected && (
        <Modal title={<>
          <div>{selected.name}</div>
          <div className="muted">{selected.birth_date} · {selected.birth_hour}時生まれ</div>
        </>} onClose={() => setSelected(null)}>
          <div className="meishiki-cards">
            <MeishikiCards analysis={selected.result_birth?.meisiki} />
          </div>
          <div className="chart">
            <FiveElementChart analysis={selected.result_birth?.gogyo} />
          </div>
          <div className="chart">
            <FiveGridRadarChart analysis={selected.result_name} />
          </div>
          {/* <div style={{ marginTop: 50 }}>
            <h4 className="font-semibold">詳細 JSON</h4>
            <pre className="result-pre">{JSON.stringify(selected, null, 2)}</pre>
          </div> */}
        </Modal>
      )}
    </main>
  )
}
