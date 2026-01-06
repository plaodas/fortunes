import React, { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import LoginModal from './LoginModal'
import { useAuth } from '../context/AuthContext'

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
    const { user, setUser, logout, refresh } = useAuth()
    const [open, setOpen] = useState(false)
    const [showLoginModal, setShowLoginModal] = useState(false)
    const [busy, setBusy] = useState(false)
    const menuRef = useRef<HTMLDivElement | null>(null)

    const closeLoginModal = useCallback(() => setShowLoginModal(false), [setShowLoginModal])

    // Auth is loaded via AuthProvider; no local fetch required

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
            await logout()
        } catch (e) {
            // ignore network errors
        }
        // Redirect to login page after clearing cookies server-side
        // logout() already redirects via provider
    }

    // login handled by LoginModal; onSuccess will call refresh/setUser as needed

    return (
        <>
            <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <div>
                    <Link href="/" style={{ fontWeight: 700, fontSize: 24, color: 'inherit', textDecoration: 'none' }}>Fortunes</Link>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }} ref={menuRef}>
                    <div>
                        {user ? (
                            <div style={{ position: 'relative' }}>
                                <Link href="/analysis" className="btn text-lg px-6 py-3">鑑定</Link>
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
                        ) : (
                            <button className="btn" onClick={() => setShowLoginModal(true)}>鑑定</button>

                        )}
                    </div>
                </div>
            </header>

            <LoginModal
                open={showLoginModal}
                onClose={closeLoginModal}
                onSuccess={async (u) => {
                    try {
                        await refresh()
                    } catch (e) {
                        // ignore
                    }
                    setShowLoginModal(false)
                    router.push('/analysis')
                }}
                redirectTo="/analysis"
            />
        </>
    )
}
