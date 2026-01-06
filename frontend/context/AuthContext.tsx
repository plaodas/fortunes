import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiFetch } from '../utils/api'
import { useRouter } from 'next/router'

type User = { username?: string; email?: string; email_verified?: boolean } | null

type AuthContextValue = {
    user: User
    loading: boolean
    // returns the raw /me payload or null
    refresh: () => Promise<any>
    setUser: (u: User) => void
    logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User>(null)
    const [loading, setLoading] = useState(true)
    const router = useRouter()

    async function refresh() {
        setLoading(true)
        try {
            const res = await apiFetch('/api/v1/auth/me', undefined, { redirectOn401: false })
            if (res.ok) {
                const data = await res.json()
                setUser({ username: data.username, email: data.email, email_verified: !!data.email_verified })
                return data
            } else {
                setUser(null)
                return null
            }
        } catch (e) {
            setUser(null)
            return null
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        void refresh()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    async function logout() {
        try {
            await apiFetch('/api/v1/auth/logout', { method: 'POST' }, { redirectOn401: false })
        } catch (e) {
            // ignore
        }
        setUser(null)
        router.replace('/login')
    }

    return (
        <AuthContext.Provider value={{ user, loading, refresh, setUser, logout }}>{children}</AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used within AuthProvider')
    return ctx
}
