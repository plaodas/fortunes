import React, { useEffect, useState } from 'react'
import Modal from '../components/Modal'
import LoadingOverlay from '../components/LoadingOverlay'
import FiveElementChart from '../components/FiveElementChart'
import FiveGridRadarChart from '../components/FiveGridRadarChart'
import MeishikiCards from '../components/MeishikiCards'
import TextWithBr from '../components/TextWithBr'

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
  meishiki: Meishiki
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
  summary: string
  detail: string
}

type AnalysisOut = {
  id: number
  name: string
  birth_date: string
  birth_hour: number
  result_birth: BirthAnalysis
  result_name: NameAnalysis
  summary: string
  detail: string
  created_at: string
}

export default function Home(): JSX.Element {
  const [name_sei, setNameSei] = useState<string>('')
  const [name_mei, setNameMei] = useState<string>('')
  const [date, setDate] = useState<string>('1990-01-01')
  const [hour, setHour] = useState<number>(12)
  const [nameSeiError, setNameSeiError] = useState<string | null>(null)
  const [nameMeiError, setNameMeiError] = useState<string | null>(null)
  const [dateError, setDateError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [history, setHistory] = useState<AnalysisOut[]>([])
  const [selected, setSelected] = useState<AnalysisOut | null>(null)
  const [loading, setLoading] = useState<boolean>(false)

  const isFormValid = !nameSeiError && !nameMeiError && !dateError && name_sei.trim().length > 0 && name_mei.trim().length > 0

  useEffect(() => {
    fetchHistory()
  }, [])
  function runValidation() {
    // name: at least 2 characters
    if (name_sei.trim().length === 0) {
      setNameSeiError('姓を入力してください')
    } else {
      setNameSeiError(null)
    }

    if (name_mei.trim().length === 0) {
      setNameMeiError('名を入力してください')
    } else {
      setNameMeiError(null)
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
  }, [name_sei, name_mei, date])

  async function submit(e: React.FormEvent) {
    e.preventDefault()

    // synchronous local validation to decide whether to submit
    const nameSeiValid = name_sei.trim().length > 0
    const nameMeiValid = name_mei.trim().length > 0
    const parsed = Date.parse(date)
    const dateValid = !isNaN(parsed) && parsed <= Date.now()

    if (!nameSeiValid || !nameMeiValid || !dateValid) {
      // set errors for user feedback
      runValidation()
      return
    }

    setLoading(true)
    try {
      // Enqueue job
      const enqueueRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyze/enqueue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name_sei, name_mei, birth_date: date, birth_hour: Number(hour) }),
      })

      if (!enqueueRes.ok) {
        // If backend returns 422, show the detail field to the user as-is
        if (enqueueRes.status === 422) {
          try {
            const data: any = await enqueueRes.json()
            const detail = data?.detail ?? JSON.stringify(data)
            alert(detail)
            setLoading(false)
            return
          } catch (e) {
            // fall through to generic handling
          }
        }

        const text = await enqueueRes.text()
        console.warn('enqueue failed', text)
        throw new Error(text || 'enqueue failed')
      }

      const { job_id } = await enqueueRes.json()
      // poll job status until complete (or timeout)
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const timeoutMs = 300_000 // 5 minutes
      const intervalMs = 5_000 // 5 seconds

      const start = Date.now()
      let finalResult: any = null

      while (Date.now() - start < timeoutMs) {
        await new Promise((r) => setTimeout(r, intervalMs))
        try {
          const st = await fetch(`${apiBase}/jobs/${job_id}`)
          if (!st.ok) {
            // continue polling on transient errors
            continue
          }
          const body = await st.json()
          // status may be like "JobStatus.complete" or "complete"
          const status = String(body.status)
          if (status.includes('complete')) {
            finalResult = body.result
            break
          }
        } catch (e) {
          // ignore and continue polling
        }
      }

      // finalResultが空のオブジェクトだった場合もエラー扱いとする
      if (finalResult === null || (typeof finalResult === 'object' && Object.keys(finalResult).length === 0)) {
        alert('鑑定中にエラーが発生しました。後でもう一度お試しください。')
      } else {
        // refresh history and select + show the new record if available
        const arr = await fetchHistory()
        if (finalResult && finalResult.id && arr) {
          const id = Number(finalResult.id)
          const found = arr.find((h) => h.id === id)
          if (found) {
            // setSelected(found)
            setResult({
              birth_analysis: {
                meishiki: found.result_birth?.meishiki,
                gogyo: found.result_birth?.gogyo,
                summary: found.summary,
              },
              name_analysis: found.result_name,
              summary: found.summary || '',
              detail: found.detail || '',
            })
          }
        }
      }
    } catch (err) {
      console.warn('analyze error', err)
      alert('鑑定中にエラーが発生しました。後でもう一度お試しください。')
    } finally {
      setLoading(false)
    }
  }

  async function fetchHistory(): Promise<AnalysisOut[] | null> {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyses`)
      if (res.ok) {
        const arr: AnalysisOut[] = await res.json()
        setHistory(arr)
        return arr
      }
    } catch (e) {
      // ignore
    }
    return null
  }

  async function deleteAnalysis(id: number) {
    if (!confirm('この鑑定を削除しますか？')) return
    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyses/${id}`
      const res = await fetch(url, { method: 'DELETE' })
      if (res.ok) {
        setHistory((prev) => prev.filter((h) => h.id !== id))
        if (selected?.id === id) setSelected(null)
      } else {
        console.warn('delete failed', await res.text())
      }
    } catch (e) {
      console.warn('delete error', e)
    }
  }

  // FiveElementChart component moved to components/FiveElementChart.tsx

  return (
    <main className="container">
      {loading && <LoadingOverlay />}
      <div className="hero card">
        <h1 className="title">Fortunes</h1>
        <p className="muted" style={{ marginTop: 8 }}>四柱推命と姓名判断から生来の運命を読み解くアプリ</p>
        <form onSubmit={submit} style={{ marginTop: 8 }}>
          <div className="form-grid">
            <div className="form-row">
              <label htmlFor="name_sei">姓</label>
              <input
                id="name_sei"
                type="text"
                className={`input ${nameSeiError ? 'invalid' : ''}`}
                value={name_sei}
                onChange={(e) => setNameSei(e.target.value)}
                aria-invalid={!!nameSeiError}
                aria-describedby={nameSeiError ? 'name-sei-error' : undefined}
                required
              />
              {nameSeiError && <div id="name-sei-error" className="error-text">{nameSeiError}</div>}
            </div>
            <div className="form-row">
              <label htmlFor="name_mei">名</label>
              <input
                id="name_mei"
                type="text"
                className={`input ${nameMeiError ? 'invalid' : ''}`}
                value={name_mei}
                onChange={(e) => setNameMei(e.target.value)}
                aria-invalid={!!nameMeiError}
                aria-describedby={nameMeiError ? 'name-mei-error' : undefined}
                required
              />
              {nameMeiError && <div id="name-mei-error" className="error-text">{nameMeiError}</div>}
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
              <button className="btn" type="submit" disabled={!isFormValid || loading}>鑑定する</button>
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
              <MeishikiCards analysis={result.birth_analysis?.meishiki} />
            </div>
            <div className="chart">
              <FiveElementChart analysis={result.birth_analysis?.gogyo} />
            </div>
            <div className="chart">
              <FiveGridRadarChart analysis={result.name_analysis} />
            </div>
            <div className="detail" style={{ marginTop: 50 }}>
              <TextWithBr text={result.detail} />
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
              <div
                key={h.id}
                className="history-item"
                onClick={() => setSelected(h)}
                role="button"
                aria-haspopup="dialog"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setSelected(h) }}
              >
                <button
                  className="history-delete"
                  onClick={(e) => { e.stopPropagation(); deleteAnalysis(h.id) }}
                  title="削除"
                  aria-label={`削除 ${h.name}`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 7h12M9 7v10a2 2 0 002 2h2a2 2 0 002-2V7M10 7V5a1 1 0 011-1h2a1 1 0 011 1v2" />
                  </svg>
                </button>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{h.name}</strong>
                    <div className="muted">{h.birth_date} · {h.birth_hour}時生まれ</div>
                  </div>
                </div>
                <div className="summary">
                  <TextWithBr text={h.summary} /></div>
              </div>
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
            <MeishikiCards analysis={selected.result_birth?.meishiki} />
          </div>
          <div className="chart">
            <FiveElementChart analysis={selected.result_birth?.gogyo} />
          </div>
          <div className="chart">
            <FiveGridRadarChart analysis={selected.result_name} />
          </div>
          <div className="detail" style={{ marginTop: 50 }}>
            <TextWithBr text={selected.detail} />
          </div>
        </Modal>
      )}
    </main>
  )
}
