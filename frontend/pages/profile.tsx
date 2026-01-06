import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import Link from 'next/link'

export default function ProfilePage(): JSX.Element {
    const [username, setUsername] = useState('')
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<string | null>(null)

    useEffect(() => {
        let mounted = true
            ; (async () => {
                try {
                    const res = await fetch('/api/v1/auth/me', { credentials: 'include' })
                    if (!mounted) return
                    if (!res.ok) {
                        setLoading(false)
                        return
                    }
                    const data = await res.json()
                    setUsername(data.username ?? '')
                    setEmail(data.email ?? '')
                } catch (e) {
                    // ignore
                } finally {
                    setLoading(false)
                }
            })()
        return () => { mounted = false }
    }, [])

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setSaving(true)
        setMessage(null)
        try {
            const res = await fetch('/api/v1/auth/update', {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email }),
            })
            if (!res.ok) {
                const txt = await res.text()
                setMessage('更新に失敗しました: ' + txt)
            } else {
                setMessage('更新しました')
            }
        } catch (e) {
            setMessage('ネットワークエラー')
        } finally {
            setSaving(false)
        }
    }

    return (
        <Layout>
            <div className="card" style={{ maxWidth: 720, margin: '0 auto' }}>
                <h1 style={{ fontSize: 20, fontWeight: 700 }}>プロフィール編集</h1>
                {loading ? (
                    <p className="muted">読み込み中...</p>
                ) : (
                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
                        <label>
                            ユーザー名
                            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} />
                        </label>
                        <label>
                            メールアドレス
                            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                        </label>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button className="btn" type="submit" disabled={saving}>保存</button>
                            <Link href="/settings" className="btn btn-ghost text-sm px-3 py-2" style={{ alignSelf: 'center' }}>パスワード変更</Link>
                        </div>
                        {message && <div className="muted">{message}</div>}
                    </form>
                )}
            </div>
        </Layout>
    )
}
