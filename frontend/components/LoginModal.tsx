import React, { useState } from 'react'
import AuthModal from './AuthModal'

type User = { username?: string; email?: string }

type Props = {
    open: boolean
    onClose: () => void
    onSuccess?: (user: User) => void
    redirectTo?: string
}

export default function LoginModal({ open, onClose, onSuccess, redirectTo }: Props) {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [message, setMessage] = useState<string | null>(null)
    const [busy, setBusy] = useState(false)

    if (!open) return null

    async function handleSubmit(e?: React.FormEvent) {
        if (e) e.preventDefault()
        setMessage(null)
        setBusy(true)
        try {
            const form = new FormData()
            form.append('username', username)
            form.append('password', password)

            const res = await fetch('/api/v1/auth/login', { method: 'POST', body: form, credentials: 'include' })
            if (!res.ok) {
                setMessage(`ログインに失敗しました: ${res.status}`)
                setBusy(false)
                return
            }

            // double-submit: read csrf cookie and call /api/v1/auth/me
            const cookies = (document.cookie || '').split(';').map((c) => c.trim())
            const csrfCookie = cookies.find((c) => c.startsWith('csrf_token='))
            const csrfValue = csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : null

            const prot = await fetch('/api/v1/auth/me', {
                method: 'GET',
                credentials: 'include',
                headers: csrfValue ? { 'x-csrf-token': csrfValue } : {}
            })

            if (!prot.ok) {
                setMessage(`保護API呼び出しに失敗: ${prot.status}`)
                setBusy(false)
                return
            }

            const data = await prot.json()
            const user = { username: data.username, email: data.email }
            setBusy(false)
            setUsername('')
            setPassword('')
            setMessage(null)
            onClose()
            if (onSuccess) onSuccess(user)
            else if (redirectTo) window.location.href = redirectTo
        } catch (err) {
            setMessage('ネットワークエラー')
            setBusy(false)
        }
    }

    return (
        <AuthModal open={open} onClose={onClose} title="ログイン">
            <form onSubmit={(e) => { e.preventDefault(); handleSubmit() }} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <input className='input' type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="ユーザー名" />
                <input className='input' type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="パスワード" />
                <div style={{ display: 'flex', gap: 8 }}>
                    <button type="submit" className="btn text-lg px-6 py-3" disabled={busy}>ログイン</button>
                    <button type="button" className="" onClick={() => { onClose(); if (redirectTo) window.location.href = `/login?next=${encodeURIComponent(redirectTo)}` }} disabled={busy}>別ページでログイン</button>
                </div>
                {message && <div className="muted" style={{ marginTop: 8 }}>{message}</div>}
            </form>
        </AuthModal>
    )
}
