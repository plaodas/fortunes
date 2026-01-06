import { useState } from "react";
import { useRouter } from 'next/router';
import Layout from "../components/Layout";
import Link from "next/link";
import { apiFetch } from '../utils/api'
import { useAuth } from '../context/AuthContext'

export default function LoginPage(): JSX.Element {
    const router = useRouter()
    const { next } = router.query as { next?: string }
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState<string | null>(null);
    const { refresh } = useAuth()

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setMessage(null);

        const form = new FormData();
        form.append("username", username);
        form.append("password", password);

        try {
            const res = await apiFetch('/api/v1/auth/login', {
                method: "POST",
                body: form,
            }, { redirectOn401: false });

            if (!res.ok) {
                setMessage(`ログインに失敗しました: ${res.status}`);
                return;
            }

            setMessage("ログインに成功しました — 保護されたAPIにアクセスします...");

            // Read csrf_token cookie (double-submit) and call protected endpoint
            const cookies = (document.cookie || "").split(";").map((c) => c.trim());
            const csrfCookie = cookies.find((c) => c.startsWith("csrf_token="));
            const csrfValue = csrfCookie ? decodeURIComponent(csrfCookie.split("=")[1]) : null;

            const prot = await apiFetch('/api/v1/auth/me', { method: "GET", headers: csrfValue ? { "x-csrf-token": csrfValue } : {} }, { redirectOn401: false })

            if (!prot.ok) {
                setMessage(`保護されたAPIの呼び出しに失敗しました: ${prot.status}`);
                return;
            }

            const data = await prot.json();
            // Refresh global auth state and redirect
            await refresh()
            try {
                router.replace((next as string) || '/analysis')
                return
            } catch (e) {
                setMessage("保護されたAPIの呼び出しに成功しました: " + JSON.stringify(data));
            }
        } catch (err) {
            setMessage("ネットワークエラー");
        }
    }

    return (
        <Layout>
            <div className="card" style={{ maxWidth: 420, margin: "0 auto" }}>
                <h1 style={{ fontSize: 20, fontWeight: 600, marginBottom: 12 }}>ログイン</h1>
                <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <input className="input" type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="ユーザー名" />
                    <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="パスワード" />
                    <button className="btn text-lg px-6 py-3" type="submit">ログイン</button>
                </form>
                <div style={{ marginTop: 12 }}>
                    <Link href="/signup" role="menuitem" style={{ padding: '8px 12px', borderRadius: 6, textDecoration: 'none', color: 'inherit' }}>アカウントをお持ちでない方は新規登録へ</Link>
                </div>
                {message && <p style={{ marginTop: 16 }}>{message}</p>}
            </div>
        </Layout>
    );
}
