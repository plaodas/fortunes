import React, { useEffect, useState } from 'react'
import { apiFetch } from '../utils/api'
import requireAuth from '../utils/ssrAuth'
import Layout from '../components/Layout'
import Modal from '../components/Modal'
import FiveElementChart from '../components/FiveElementChart'
import FiveGridRadarChart from '../components/FiveGridRadarChart'
import MeishikiCards from '../components/MeishikiCards'
import TextWithBr from '../components/TextWithBr'
import TimeZoneSelector from '../components/TimeZoneSelector'
import { birthCaption, SHICHEN } from '../lib/readingDisplay'

type Meishiki = {
    year?: string
    month?: string
    day?: string
    hour?: string
    strength?: string
    pillars?: {
        year?: { tsuhen?: string; juniun?: string }
        month?: { tsuhen?: string; juniun?: string }
        day?: { tsuhen?: string; juniun?: string }
        hour?: { tsuhen?: string; juniun?: string }
    }
    daiun?: { start: string; kanshi: string; tsuhen: string }[]
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
    birth_date: string
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
    birth_tz: string
    result_birth: BirthAnalysis
    result_name: NameAnalysis
    summary: string
    detail: string
    created_at: string
}

export default function Analysis(): JSX.Element {
    const [name_sei, setNameSei] = useState<string>('')
    const [name_mei, setNameMei] = useState<string>('')
    const [date, setDate] = useState<string>('1990-01-01')
    const [hour, setHour] = useState<number>(11)
    const [nameSeiError, setNameSeiError] = useState<string | null>(null)
    const [nameMeiError, setNameMeiError] = useState<string | null>(null)
    const [dateError, setDateError] = useState<string | null>(null)
    const [result, setResult] = useState<AnalysisResult | null>(null)
    const [history, setHistory] = useState<AnalysisOut[]>([])
    const [selected, setSelected] = useState<AnalysisOut | null>(null)
    const [loading, setLoading] = useState<boolean>(false)
    const [birthTz, setBirthTz] = useState<string>('Asia/Tokyo')
    const [abroad, setAbroad] = useState<boolean>(false)
    const [sex, setSex] = useState<string>('')
    const [storyError, setStoryError] = useState<string | null>(null)
    const [elapsed, setElapsed] = useState<number>(0)

    const isFormValid = !nameSeiError && !nameMeiError && !dateError && name_sei.trim().length > 0 && name_mei.trim().length > 0 && (sex === 'male' || sex === 'female')

    useEffect(() => {
        fetchHistory()
    }, [])

    useEffect(() => {
        if (!loading) return
        setElapsed(0)
        const started = Date.now()
        const id = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
        return () => window.clearInterval(id)
    }, [loading])
    function runValidation() {
        // name: at least 2 characters
        const name_sei_length = name_sei.trim().length
        if (name_sei_length === 0) {
            setNameSeiError('姓を入力してください')
        } else if (name_sei_length > 50) {
            setNameSeiError('姓は50文字以内で入力してください')
        } else {
            setNameSeiError(null)
        }
        const name_mei_length = name_mei.trim().length
        if (name_mei_length === 0) {
            setNameMeiError('名を入力してください')
        } else if (name_mei_length > 50) {
            setNameMeiError('名は50文字以内で入力してください')
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

    async function submit(e?: React.FormEvent) {
        e?.preventDefault()

        // synchronous local validation to decide whether to submit
        const nameSeiValid = name_sei.trim().length > 0 && name_sei.trim().length <= 50
        const nameMeiValid = name_mei.trim().length > 0 && name_mei.trim().length <= 50
        const parsed = Date.parse(date)
        const dateValid = !isNaN(parsed) && parsed <= Date.now()

        if (!nameSeiValid || !nameMeiValid || !dateValid) {
            // set errors for user feedback
            runValidation()
            return
        }

        setStoryError(null)
        setLoading(true)
        try {
            const enqueueRes = await apiFetch('/api/v1/analyze/enqueue', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name_sei, name_mei, birth_date: date, birth_hour: Number(hour), birth_tz: birthTz, sex }),
            })

            if (!enqueueRes.ok) {
                if (enqueueRes.status === 422) {
                    try {
                        const data: any = await enqueueRes.json()
                        setStoryError(data?.detail ?? JSON.stringify(data))
                        return
                    } catch (e) {
                        // fall through to generic handling
                    }
                }
                const text = await enqueueRes.text()
                console.warn('enqueue failed', text)
                throw new Error(text || 'enqueue failed')
            }

            const data = await enqueueRes.json()
            setResult({
                birth_date: date,
                birth_analysis: {
                    meishiki: data.result_birth?.meishiki,
                    gogyo: data.result_birth?.gogyo,
                },
                name_analysis: data.result_name,
                summary: '',
                detail: '',
            })

            const outcome = await pollJob(data.job_id)
            if (outcome === 'error') {
                setStoryError('物語を作成できませんでした。もう一度お試しください。')
                return
            }
            const arr = await fetchHistory()
            const found = arr?.find((h) => h.id === outcome.id)
            if (!found) {
                setStoryError('物語を作成できませんでした。もう一度お試しください。')
                return
            }
            setResult({
                birth_date: found.birth_date,
                birth_analysis: {
                    meishiki: found.result_birth?.meishiki,
                    gogyo: found.result_birth?.gogyo,
                    summary: found.summary,
                },
                name_analysis: found.result_name,
                summary: found.summary || '',
                detail: found.detail || '',
            })
        } catch (err) {
            console.warn('analyze error', err)
            setStoryError('物語を作成できませんでした。もう一度お試しください。')
        } finally {
            setLoading(false)
        }
    }

    async function pollJob(jobId: string): Promise<{ id: number } | 'error'> {
        const timeoutMs = 1_200_000
        const intervalMs = 5_000
        const start = Date.now()
        while (Date.now() - start < timeoutMs) {
            await new Promise((r) => setTimeout(r, intervalMs))
            try {
                const st = await apiFetch(`/api/v1/jobs/${jobId}`)
                if (!st.ok) continue
                const body = await st.json()
                const status = String(body.status)
                if (status.includes('not_found')) return 'error'
                if (!status.includes('complete')) continue
                const finished = body.result
                if (finished && typeof finished === 'object' && finished.id) return { id: Number(finished.id) }
                return 'error'
            } catch (e) {
                // keep polling
            }
        }
        return 'error'
    }

    async function fetchHistory(): Promise<AnalysisOut[] | null> {
        try {
            const res = await apiFetch('/api/v1/analyses')
            if (res.status === 401) return null
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
            const url = `/api/v1/analyses/${id}`
            const res = await apiFetch(url, { method: 'DELETE' })
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

    return (
        <Layout hero={(
            <div className="hero card">
                <p className="" style={{ marginTop: 8 }}>お名前と生年月日、生まれた時間、性別を入力して［鑑定する］ボタンを押してください</p>
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
                                {SHICHEN.map((item) => (
                                    <option key={item.branch} value={String(item.hour)}>{item.branch}（{item.range}）</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-row">
                            <label htmlFor="sex">性別</label>
                            <select
                                id="sex"
                                className="input"
                                value={sex}
                                onChange={(e) => setSex(e.target.value)}
                                required
                            >
                                <option value="">選択してください</option>
                                <option value="male">男性</option>
                                <option value="female">女性</option>
                            </select>
                        </div>
                        <div className="form-row">
                            <label htmlFor="abroad">
                                <input
                                    id="abroad"
                                    type="checkbox"
                                    checked={abroad}
                                    onChange={(e) => {
                                        setAbroad(e.target.checked)
                                        if (!e.target.checked) setBirthTz('Asia/Tokyo')
                                    }}
                                />
                                日本以外で生まれた
                            </label>
                        </div>
                        {abroad && <TimeZoneSelector birthTz={birthTz} setBirthTz={setBirthTz} />}
                        <div className="form-action" style={{ alignSelf: 'end' }}>
                            <button className="btn" type="submit" disabled={!isFormValid || loading}>鑑定する</button>
                        </div>
                    </div>
                </form>
            </div>
        )}>
            {(result || storyError) && (
                <section style={{ marginTop: 16 }}>
                    <div className="card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 className="text-2xl font-bold">鑑定結果</h2>
                        </div>
                        {loading && (
                            <p className="story-pending" role="status" aria-live="polite">
                                <span className="story-pending-spin" aria-hidden="true" />
                                物語を作成中です（{elapsed}秒）
                            </p>
                        )}
                        <div className="detail">
                            {storyError && (
                                <div className="story-status">
                                    <p>{storyError}</p>
                                    <button type="button" className="btn" onClick={() => submit()}>もう一度作成する</button>
                                </div>
                            )}
                            {result?.detail ? <TextWithBr text={result.detail} /> : null}
                        </div>
                        {result && (
                            <>
                                <div className="meishiki-cards">
                                    <MeishikiCards analysis={result.birth_analysis?.meishiki} birthDate={result.birth_date} />
                                </div>
                                <div className="chart">
                                    <FiveElementChart analysis={result.birth_analysis?.gogyo} />
                                </div>
                                <div className="chart">
                                    <FiveGridRadarChart analysis={result.name_analysis} />
                                </div>
                            </>
                        )}
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
                                        <div className="muted">{birthCaption(h.birth_date, h.birth_hour, h.birth_tz)}</div>
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
                    <div className="muted">{birthCaption(selected.birth_date, selected.birth_hour, selected.birth_tz)}</div>
                </>} onClose={() => setSelected(null)}>
                    <div className="detail">
                        <TextWithBr text={selected.detail} />
                    </div>
                    <div className="meishiki-cards">
                        <MeishikiCards analysis={selected.result_birth?.meishiki} birthDate={selected.birth_date} />
                    </div>
                    <div className="chart">
                        <FiveElementChart analysis={selected.result_birth?.gogyo} />
                    </div>
                    <div className="chart">
                        <FiveGridRadarChart analysis={selected.result_name} />
                    </div>
                </Modal>
            )}
        </Layout>
    )
}

export const getServerSideProps = requireAuth
