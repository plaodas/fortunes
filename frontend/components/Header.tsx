import React, { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import AuthModal from './AuthModal'

type User = {
    username?: string
    email?: string
}

function initialsFromName(name?: string) {
    if (!name) return 'U'
    const parts = name.split(/[\s_\-@.]+/).filter(Boolean)
    if (parts.length === 0) return name.slice(0, 1).toUpperCase()
    if (parts.length === 1) return parts[0].slice(0, 1).toUpperCase()
    return (parts[0].slice(0, 1) + parts[1].slice(0, 1)).toUpperCase()
}

export default function Header(): JSX.Element {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [open, setOpen] = useState(false)
    const [showLoginModal, setShowLoginModal] = useState(false)
    const [loginUsername, setLoginUsername] = useState('')
    const [loginPassword, setLoginPassword] = useState('')
    const [loginMessage, setLoginMessage] = useState<string | null>(null)
    const [busy, setBusy] = useState(false)
    const menuRef = useRef<HTMLDivElement | null>(null)

    const closeLoginModal = useCallback(() => setShowLoginModal(false), [setShowLoginModal])

    useEffect(() => {
        let mounted = true
            ; (async () => {
                try {
                    const res = await fetch('/api/v1/auth/me', { credentials: 'include' })
                    if (!mounted) return
                    if (!res.ok) {
                        return
                    }
                    const data = await res.json()
                    setUser({ username: data.username })
                } catch (e) {
                    // ignore
                }
            })()
        return () => { mounted = false }
    }, [])

    useEffect(() => {
        function onDoc(e: MouseEvent) {
            if (!menuRef.current) return
            if (e.target instanceof Node && !menuRef.current.contains(e.target)) setOpen(false)
        }
        document.addEventListener('click', onDoc)
        return () => document.removeEventListener('click', onDoc)
    }, [])

    async function handleLogout() {
        if (busy) return
        setBusy(true)
        try {
            await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
        } catch (e) {
            // ignore network errors
        }
        // Redirect to login page after clearing cookies server-side
        router.replace('/login')
    }

    async function handleLoginSubmit(e?: React.FormEvent) {
        if (e) e.preventDefault()
        setLoginMessage(null)
        try {
            const form = new FormData()
            form.append('username', loginUsername)
            form.append('password', loginPassword)
            const res = await fetch('/api/v1/auth/login', { method: 'POST', body: form, credentials: 'include' })
            if (!res.ok) {
                setLoginMessage(`ログインに失敗しました: ${res.status}`)
                return
            }

            // read csrf cookie and call /api/v1/auth/me to confirm
            const cookies = (document.cookie || '').split(';').map((c) => c.trim())
            const csrfCookie = cookies.find((c) => c.startsWith('csrf_token='))
            const csrfValue = csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : null

            const prot = await fetch('/api/v1/auth/me', { method: 'GET', credentials: 'include', headers: csrfValue ? { 'x-csrf-token': csrfValue } : {} })
            if (!prot.ok) {
                setLoginMessage(`保護API呼び出しに失敗: ${prot.status}`)
                return
            }
            const data = await prot.json()
            setUser({ username: data.username })
            setShowLoginModal(false)
            setLoginUsername('')
            setLoginPassword('')
            setLoginMessage(null)
            // navigate to analysis if intended
            router.push('/analysis')
        } catch (err) {
            setLoginMessage('ネットワークエラー')
        }
    }

    return (
        <>
            <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <div>
                    <Link href="/" style={{ fontWeight: 700, fontSize: 24, color: 'inherit', textDecoration: 'none' }}>Fortunes</Link>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }} ref={menuRef}>
                    <div>
                        {user ? (
                            <>
                                <Link href="/analysis" className="btn" style={{ textDecoration: 'none' }}>鑑定</Link>
                                <div style={{ position: 'relative' }}>
                                    <button
                                        aria-haspopup="true"
                                        aria-expanded={open}
                                        onClick={() => setOpen((v) => !v)}
                                        style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: 8,
                                            background: 'transparent',
                                            border: 'none',
                                            cursor: 'pointer',
                                        }}
                                    >
                                        <span style={{
                                            width: 36,
                                            height: 36,
                                            borderRadius: 18,
                                            background: '#eef2ff',
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontWeight: 700,
                                            color: '#3730a3'
                                        }}>{initialsFromName(user?.username)}</span>
                                        <span className="muted" style={{ fontSize: 14 }}>{user?.username ?? 'ログイン'}</span>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ transform: open ? 'rotate(180deg)' : 'none' }}>
                                            <path d="M19 9l-7 7-7-7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                    </button>

                                    {open && (
                                        <div role="menu" style={{ position: 'absolute', right: 0, top: 'calc(100% + 8px)', minWidth: 180, background: 'white', boxShadow: '0 8px 24px rgba(15,23,42,0.12)', borderRadius: 8, padding: 8, zIndex: 60 }}>
                                            <div style={{ padding: '8px 12px', borderRadius: 6 }}>
                                                <div style={{ fontWeight: 700 }}>{user?.username ?? 'ゲスト'}</div>
                                                <div className="muted" style={{ fontSize: 13 }}>{user?.email ?? ''}</div>
                                            </div>
                                            <hr style={{ border: 'none', borderTop: '1px solid #f1f5f9', margin: '8px 0' }} />
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                                <Link href="/profile" role="menuitem" style={{ padding: '8px 12px', borderRadius: 6, textDecoration: 'none', color: 'inherit' }}>プロフィール</Link>
                                                <Link href="/settings" role="menuitem" style={{ padding: '8px 12px', borderRadius: 6, textDecoration: 'none', color: 'inherit' }}>設定</Link>
                                                <button onClick={handleLogout} role="menuitem" style={{ padding: '8px 12px', borderRadius: 6, textAlign: 'left', background: 'transparent', border: 'none', color: '#dc2626', cursor: 'pointer' }} disabled={busy}>ログアウト</button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </>
                        ) : (
                            <button className="btn" onClick={() => setShowLoginModal(true)}>鑑定</button>
                        )}
                    </div>
                </div>
            </header>

            {showLoginModal && (
                <AuthModal open={showLoginModal} onClose={closeLoginModal} title="ログイン">
                    <form onSubmit={(e) => { e.preventDefault(); handleLoginSubmit() }} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <input className="input" value={loginUsername} onChange={(e) => setLoginUsername(e.target.value)} placeholder="ユーザー名" />
                        <input className="input" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} placeholder="パスワード" type="password" />
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button type="submit" className="btn">ログイン</button>
                        </div>
                        {loginMessage && <div className="muted" style={{ marginTop: 8 }}>{loginMessage}</div>}
                    </form>
                </AuthModal>
            )}
        </>
    )
}
