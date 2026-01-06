import { useState, useEffect } from "react";
import Link from 'next/link'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { apiFetch } from '../utils/api'
import { filterUsernameInput, isValidUsername } from '../utils/validation'

function validateEmail(email: string) {
    // simple RFC-ish check
    return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email);
}

function validatePassword(pw: string) {
    const min = 8;
    if (pw.length < min) return `パスワードは最低 ${min} 文字必要です`;
    if (!/[0-9]/.test(pw) || !/[A-Za-z]/.test(pw)) return "パスワードは英字と数字を含めてください";
    return null;
}

export default function SignupPage(): JSX.Element {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");
    const [displayName, setDisplayName] = useState("");
    const [message, setMessage] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [errors, setErrors] = useState<{ [k: string]: string | null }>({});
    const { refresh } = useAuth()

    function runValidation() {
        const e: { [k: string]: string | null } = {};
        if (!username.trim()) e.username = "ユーザー名は必須です";
        else if (!isValidUsername(username.trim())) e.username = "ユーザー名に使用できない文字が含まれています";
        else if (username.trim().length < 3) e.username = "ユーザー名は3文字以上必要です";

        if (!email.trim()) e.email = "メールアドレスは必須です";
        else if (!validateEmail(email.trim())) e.email = "メールアドレスの形式が正しくありません";

        const pwErr = validatePassword(password);
        if (!password) e.password = "パスワードは必須です";
        else if (pwErr) e.password = pwErr;

        if (displayName && displayName.length > 50) e.displayName = "表示名は50文字以内で入力してください";

        setErrors(e);
        // return true if no errors
        return Object.keys(e).length === 0;
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setMessage(null);
        if (!runValidation()) {
            setMessage("エラーを修正してください");
            return;
        }

        setSubmitting(true);
        try {
            const res = await apiFetch('/api/v1/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username.trim(), password, email: email.trim(), display_name: displayName || undefined }),
            }, { redirectOn401: false });

            if (!res.ok) {
                const text = await res.text();
                setMessage(`登録に失敗しました: ${res.status} ${text}`);
                setSubmitting(false);
                return;
            }
            setMessage("登録に成功しました — 確認メールを送信しました。メール内のリンクをクリックしてアカウントを有効化してください。");
            // Attempt to refresh auth state in case server set cookies
            try {
                const me = await refresh()
                // Only redirect to analysis if email has been verified
                if (me && me.email_verified) {
                    // eslint-disable-next-line @typescript-eslint/no-floating-promises
                    (window.location.pathname && window.location.replace('/analysis'))
                }
            } catch (e) {
                // ignore
            }
        } catch (err) {
            setMessage('ネットワークエラー');
        } finally {
            setSubmitting(false);
        }
    }

    // immediate validation: re-run validation as fields change
    useEffect(() => {
        // runValidation will update `errors` state; we don't set message here
        runValidation();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [username, email, password, displayName]);

    const hasErrors = Object.keys(errors).length > 0;

    return (
        <Layout>
            <div className="card" style={{ maxWidth: 420, margin: '0 auto' }}>
                <h1 style={{ fontSize: 20, fontWeight: 600, marginBottom: 12 }}>新規登録</h1>
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 8 }} noValidate>
                    <div>
                        <input className="input" type="text" style={{ width: '100%' }} value={username} onChange={(e) => setUsername(filterUsernameInput(e.target.value))} placeholder="ユーザー名" />
                        <div className="muted" style={{ fontSize: 12 }}>使用可能な文字: 半角英数字と記号（スペース不可）</div>
                        {errors.username && <div style={{ color: 'red', fontSize: 12 }}>{errors.username}</div>}
                    </div>

                    <div>
                        <input className="input" type="text" style={{ width: '100%' }} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="メールアドレス" />
                        {errors.email && <div style={{ color: 'red', fontSize: 12 }}>{errors.email}</div>}
                    </div>

                    <div>
                        <input className="input" type="password" style={{ width: '100%' }} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="パスワード" />
                        {errors.password && <div style={{ color: 'red', fontSize: 12 }}>{errors.password}</div>}
                    </div>

                    <div>
                        <input className="input" type="text" style={{ width: '100%' }} value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="表示名 (任意)" />
                        {errors.displayName && <div style={{ color: 'red', fontSize: 12 }}>{errors.displayName}</div>}
                    </div>

                    <button className="btn text-lg px-6 py-3" type="submit" disabled={submitting || hasErrors}>{submitting ? '登録中…' : 'アカウント作成'}</button>
                </form>
                {message && <p style={{ marginTop: 16 }}>{message}</p>}
                <div style={{ marginTop: 12 }}>
                    <Link href="/login" role="menuitem" style={{ padding: '8px 12px', borderRadius: 6, textDecoration: 'none', color: 'inherit' }}>既にアカウントをお持ちの場合はログインへ</Link>
                </div>
            </div>
        </Layout>
    );
}
