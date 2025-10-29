import React, {useState} from 'react'
import './styles.css'

export default function App(){
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)

  const upload = async () => {
    if(!file) return
    setLoading(true)
    const form = new FormData()
    form.append('file', file)
    try{
      const res = await fetch('http://localhost:8000/process/', { method: 'POST', body: form })
      if(!res.ok) throw new Error('Processing failed')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `reconstructed_${file.name}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    }catch(e){
      alert(e.message || 'Error')
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>Aduragbemi Smart Reader</h1>
      <div className="uploader">
        <input type="file" accept="application/pdf,image/*" onChange={e=>setFile(e.target.files[0])} />
        <div className="controls">
          <button onClick={upload} disabled={!file || loading}>{loading? 'Processing...':'Upload & Download Extracted PDF'}</button>
        </div>
      </div>

      <div className="placeholders">
        <button onClick={()=>alert('Read Aloud coming soon (placeholder)')}>🔊 Read Aloud</button>
        <button onClick={()=>alert('Ask the PDF coming soon (placeholder)')}>🤖 Ask the PDF</button>
      </div>
    </div>
  )
}
