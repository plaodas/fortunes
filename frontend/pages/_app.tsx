import type { AppProps } from 'next/app'
import '../styles/globals.css'

const inlineStyles = `
/* Fallback inline styles - ensure styling in dev when external CSS fails */
:root{--bg:#f8fafc;--card:#ffffff;--muted:#6b7280;--accent:#4f46e5;--radius:10px}
*{box-sizing:border-box}html,body,#__next{height:100%}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial;background:linear-gradient(180deg,var(--bg),#eef2ff);color:#0f172a;-webkit-font-smoothing:antialiased}
.container{max-width:960px;margin:40px auto;padding:24px}.card{background:var(--card);border-radius:var(--radius);box-shadow:0 6px 18px rgba(15,23,42,0.06);padding:16px}.form-grid{display:grid;gap:12px;grid-template-columns:1fr 1fr}.form-row{display:flex;flex-direction:column}label{font-size:14px;color:var(--muted)}input[type="text"],input[type="date"],input[type="number"]{padding:10px 12px;border-radius:8px;border:1px solid #e6edf7;margin-top:6px;font-size:14px}button.btn{background:var(--accent);color:white;padding:10px 14px;border-radius:8px;border:none;font-weight:600;cursor:pointer}.result-pre{background:#f8fafc;padding:12px;border-radius:8px;margin-top:12px;font-family:monospace}.history{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px}.history-item{padding:12px;border-radius:8px;background:linear-gradient(180deg,#fff,#fbfdff);border:1px solid #f1f5f9}.muted{color:var(--muted);font-size:13px}.summary{margin-top:8px;color:#334155}.chart{display:flex;gap:8px;align-items:end;height:120px;margin-top:8px}.bar{width:40px;background:var(--accent);border-radius:6px}
`

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: inlineStyles }} />
      <Component {...pageProps} />
    </>
  )
}
