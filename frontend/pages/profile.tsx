import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import Link from 'next/link'
import { apiFetch } from '../utils/api'
import requireAuth from '../utils/ssrAuth'
import { useAuth } from '../context/AuthContext'
import { useRouter } from 'next/router'

export default function ProfilePage(): JSX.Element {
    const [username, setUsername] = useState('')
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<string | null>(null)


    const router = useRouter()
    const { logout, refresh } = useAuth()

    useEffect(() => {
        let mounted = true
            ; (async () => {
                try {
                    const res = await apiFetch('/api/v1/auth/me')
                    if (!mounted) return
                    if (res.status === 401) {
                        // apiFetch triggers redirect; stop rendering
                        return
                    }
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
            const res = await apiFetch('/api/v1/auth/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email }),
            }, { redirectOn401: false })
            if (res.status === 401) {
                setMessage('認証が必要です。再ログインしてください')
                return
            }
            if (!res.ok) {
                const txt = await res.text()
                setMessage('更新に失敗しました: ' + txt)
            } else {
                // parse returned user info; backend returns new token and profile
                const data = await res.json()
                setMessage('更新しました')
                // update local form state with authoritative values
                if (data.username) setUsername(data.username)
                if (data.email) setEmail(data.email)
                // Refresh global auth state so frontend picks up rotated cookies/token
                try {
                    await refresh()
                } catch (e) {
                    // ignore - user will be redirected if not authenticated
                }
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
                        <label style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <span style={{ minWidth: 80, display: 'inline-block' }}>ユーザー名</span>
                            <input className="input" style={{ flex: 1 }} type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="ユーザー名" />
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <span style={{ minWidth: 80, display: 'inline-block' }}>メールアドレス</span>
                            <input className="input" style={{ flex: 1 }} type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="メールアドレス" />
                        </label>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button className="btn" type="submit" disabled={saving}>保存</button>
                            <Link href="/settings" style={{ alignSelf: 'center' }}>パスワード変更へ</Link>
                        </div>
                        {message && <div className="muted">{message}</div>}
                    </form>
                )}
            </div>
        </Layout>
    )
}

export const getServerSideProps = requireAuth
