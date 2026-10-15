import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ImagePlus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, errMsg } from '../api'

export default function Report() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { data: cats = [] } = useQuery({ queryKey: ['cats'], queryFn: async () => (await api.get<string[]>('/items/meta/categories')).data })
  const [kind, setKind] = useState<'lost' | 'found'>('lost')
  const [form, setForm] = useState({ title: '', description: '', category: 'other', location: '', event_time: new Date().toISOString().slice(0, 16), secret_detail: '' })
  const [image, setImage] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true); setError('')
    const fd = new FormData()
    fd.append('kind', kind)
    Object.entries({ ...form, event_time: new Date(form.event_time).toISOString() }).forEach(([k, v]) => { if (v) fd.append(k, v) })
    if (image) fd.append('image', image)
    try {
      const r = await api.post('/items', fd)
      qc.invalidateQueries()
      navigate(`/items/${r.data.id}`)
    } catch (err) { setError(errMsg(err)) } finally { setBusy(false) }
  }

  return (
    <form onSubmit={submit} className="card mx-auto max-w-2xl space-y-5 p-6">
      <h1 className="text-xl font-bold">Report an item</h1>
      <div className="grid grid-cols-2 gap-2 rounded-lg bg-white/[0.07] p-1">
        {(['lost', 'found'] as const).map((k) => (
          <button type="button" key={k} onClick={() => setKind(k)} className={`rounded-md py-2 text-sm font-medium ${kind === k ? 'bg-white/[0.04] shadow-sm' : 'text-slate-400'}`}>
            {k === 'lost' ? 'I lost something' : 'I found something'}
          </button>
        ))}
      </div>
      <div><label className="label">Title</label><input className="input" required minLength={3} value={form.title} onChange={set('title')} placeholder="e.g. Black Dell laptop" /></div>
      <div><label className="label">Description</label><textarea className="input" rows={3} value={form.description} onChange={set('description')} placeholder="Colour, brand, marks, contents…" /></div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div><label className="label">Category</label><select className="input" value={form.category} onChange={set('category')}>{cats.map((c) => <option key={c}>{c}</option>)}</select></div>
        <div><label className="label">Location</label><input className="input" required value={form.location} onChange={set('location')} placeholder="Central Library" /></div>
      </div>
      <div><label className="label">When was it {kind === 'lost' ? 'lost' : 'found'}?</label><input type="datetime-local" className="input" required value={form.event_time} onChange={set('event_time')} /></div>
      {kind === 'found' && (
        <div className="rounded-lg border border-amber-400/30 bg-amber-400/10 p-4">
          <label className="label text-amber-200">Secret verification detail</label>
          <input className="input" required value={form.secret_detail} onChange={set('secret_detail')} placeholder="Something only the real owner would know, e.g. a scratch, wallpaper, sticker" />
          <p className="mt-1 text-xs text-amber-300">Hidden from everyone but you. Claimants must describe it, and we score how well they match.</p>
        </div>
      )}
      <div>
        <label className="label">Photo (optional)</label>
        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-white/15 p-4 text-sm text-slate-400 hover:bg-white/[0.07]">
          <ImagePlus size={20} />{image ? image.name : 'Choose JPEG, PNG or WEBP (max 5MB)'}
          <input type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => setImage(e.target.files?.[0] ?? null)} />
        </label>
        {image && <img src={URL.createObjectURL(image)} alt="preview" className="mt-3 h-40 rounded-lg object-cover" />}
      </div>
      {error && <p className="rounded-lg bg-rose-400/10 px-3 py-2 text-sm text-rose-300">{error}</p>}
      <button className="btn w-full" disabled={busy}>{busy ? 'Submitting…' : 'Submit report'}</button>
    </form>
  )
}
