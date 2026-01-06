import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from 'next/link'

export default function ConfirmEmailPage(): JSX.Element {
    const router = useRouter();
    const { token } = router.query as { token?: string };
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;
        async function confirm() {
            setStatus('loading');
            try {
                const url = `/api/v1/auth/confirm-email?token=${encodeURIComponent(token as string)}`;
                const res = await fetch(url, { method: 'GET', credentials: 'include' });
                if (res.ok) {
                    const body = await res.json().catch(() => null);
                    setMessage('メールアドレスを確認しました。');
                    setStatus('success');
                    // redirect to home after short delay
                    setTimeout(() => router.push('/'), 2000);
                } else {
                    const text = await res.text();
                    setMessage(`確認に失敗しました: ${res.status} ${text}`);
                    setStatus('error');
                }
            } catch (err) {
                setMessage('ネットワークエラーが発生しました');
                setStatus('error');
            }
        }
        confirm();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    return (
        <div style={{ padding: 24, maxWidth: 640, margin: '0 auto' }}>
            <h1 style={{ fontSize: 20, fontWeight: 600, marginBottom: 12 }}>メールアドレスの確認</h1>
            {status === 'idle' && <p>トークンを検出しています…</p>}
            {status === 'loading' && <p>確認中…</p>}
            {status === 'success' && (
                <div>
                    <p style={{ color: 'green' }}>{message}</p>
                    <p>トップページへ移動します…</p>
                    <p><Link href="/" className="btn text-sm px-4 py-2">今すぐ移動</Link></p>
                </div>
            )}
            {status === 'error' && (
                <div>
                    <p style={{ color: 'red' }}>{message}</p>
                    <p>問題が続く場合はサポートに連絡してください。</p>
                    <p>
                        <Link href="/signup" className="btn text-sm px-3 py-2">再登録</Link>
                        <span style={{ margin: '0 8px' }}>または</span>
                        <Link href="/login" className="btn text-sm px-3 py-2">ログイン</Link>
                    </p>
                </div>
            )}
        </div>
    );
}
