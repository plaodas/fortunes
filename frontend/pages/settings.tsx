import React, { useState } from 'react'
import Header from '../components/Header'
import Link from 'next/link'

export default function SettingsPage(): JSX.Element {
    const [currentPassword, setCurrentPassword] = useState('')
    const [newPassword, setNewPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<string | null>(null)

    async function handlePasswordChange(e: React.FormEvent) {
        e.preventDefault()
        setMessage(null)
        if (newPassword !== confirmPassword) {
            setMessage('新しいパスワードが一致しません')
            return
        }
        setSaving(true)
        try {
            const res = await fetch('/api/v1/auth/change-password', {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
            })
            if (!res.ok) {
                const txt = await res.text()
                setMessage('変更に失敗しました: ' + txt)
            } else {
                setMessage('パスワードを更新しました')
                setCurrentPassword('')
                setNewPassword('')
                setConfirmPassword('')
            }
        } catch (e) {
            setMessage('ネットワークエラー')
        } finally {
            setSaving(false)
        }
    }

    return (
        <main className="container">
            <Header />
            <div className="card" style={{ maxWidth: 720, margin: '0 auto' }}>
                <h1 style={{ fontSize: 20, fontWeight: 700 }}>パスワード設定</h1>
                <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
                    <label>
                        現在のパスワード
                        <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
                    </label>
                    <label>
                        新しいパスワード
                        <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                    </label>
                    <label>
                        新しいパスワード（確認）
                        <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
                    </label>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button className="btn" type="submit" disabled={saving}>変更</button>
                        <Link href="/profile" style={{ alignSelf: 'center' }}>プロフィールへ</Link>
                    </div>
                    {message && <div className="muted">{message}</div>}
                </form>
            </div>
        </main>
    )
}
