import {useState} from 'react'

export default function Home() {
  const [name, setName] = useState('')
  const [date, setDate] = useState('1990-01-01')
  const [hour, setHour] = useState(12)
  const [result, setResult] = useState(null)

  async function submit(e) {
    e.preventDefault()
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyze`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, birth_date: date, birth_hour: Number(hour)})
    })
    const body = await res.json()
    setResult(body.result)
  }

  function FiveElementChart(analysis) {
    if (!analysis) return null
    // derive five-element values from the numeric nameAnalysis fields as a placeholder
    const vals = [analysis.tenkaku, analysis.jinkaku, analysis.chikaku, analysis.gaikaku, analysis.soukaku]
    const labels = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']
    const max = Math.max(...vals, 1)
    return (
      <div style={{display:'flex', gap:8, alignItems:'end', height:120}}>
        {vals.map((v,i)=> (
          <div key={i} style={{textAlign:'center'}}>
            <div style={{width:40, height: Math.round((v/max)*100), background:'#4f46e5', margin:'0 auto'}}></div>
            <div style={{fontSize:12}}>{labels[i]}</div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <main style={{padding:24,fontFamily:'sans-serif',maxWidth:720,margin:'0 auto'}}>
      <h1>Fortunes - MVP</h1>
      <form onSubmit={submit} style={{display:'grid',gap:8,maxWidth:420}}>
        <label>Name <input value={name} onChange={e=>setName(e.target.value)} required/></label>
        <label>Birth date <input type='date' value={date} onChange={e=>setDate(e.target.value)} required/></label>
        <label>Birth hour <input type='number' min={0} max={23} value={hour} onChange={e=>setHour(e.target.value)} required/></label>
        <button type='submit'>Analyze</button>
      </form>

      {result && (
        <section style={{marginTop:24}}>
          <h2>Result</h2>
          <pre style={{background:'#f3f4f6',padding:12}}>{JSON.stringify(result,null,2)}</pre>
          <h3>五行バランス (placeholder)</h3>
          {FiveElementChart(result.nameAnalysis)}
        </section>
      )}
    </main>
  )
}
