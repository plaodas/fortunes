import React from 'react'
import Link from 'next/link'
import Header from '../components/Header'

export default function Home(): JSX.Element {
  return (
    <main className="container">
      <Header />

      <div className="hero card" style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: 28, marginBottom: 8 }}>Fortunes</h1>
        <p style={{ marginBottom: 16 }}>四柱推命と姓名判断から生来の運命を読み解くアプリです。</p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 8 }}>
          <Link href="/login" className="btn">ログイン</Link>
          <Link href="/signup" className="btn btn-ghost">新規登録</Link>
        </div>

        <p className="muted">ログインまたは新規登録して鑑定をお試しください。</p>
      </div>

      <footer style={{ marginTop: 24, textAlign: 'center' }}>
        <Link href="/terms" className="muted">利用規約</Link>
        <span style={{ margin: '0 8px' }}>・</span>
        <Link href="/privacy" className="muted">プライバシーポリシー</Link>
      </footer>
    </main>
  )
}

