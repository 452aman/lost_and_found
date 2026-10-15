import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, errMsg } from '../api'
import { useAuth } from '../auth'
import { KindBadge, StatusBadge } from '../components/ItemCard'
import type { Item } from '../types'

export default function ItemDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [answer, setAnswer] = useState('')
  const { data: item, isLoading } = useQuery({ queryKey: ['item', id], queryFn: async () => (await api.get<Item>(`/items/${id}`)).data })
  const claim = useMutation({
    mutationFn: async () => (await api.post(`/items/${id}/claims`, { answer })).data,
    onSuccess: () => { setAnswer(''); qc.invalidateQueries({ queryKey: ['claims'] }) },
  })
  const remove = useMutation({ mutationFn: async () => api.delete(`/items/${id}`), onSuccess: () => { qc.invalidateQueries(); navigate('/browse') } })
  if (isLoading || !item) return <p className="text-slate-400">Loading…</p>
  const mine = item.owner.id === user?.id

  return (
    <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-5">
      <div className="card overflow-hidden md:col-span-2">
        {item.image_url ? <img src={item.image_url} alt={item.title} className="h-full max-h-96 w-full object-cover" />
          : <div className="flex h-64 items-center justify-center bg-white/[0.07] text-6xl">{item.kind === 'lost' ? '🔍' : '📦'}</div>}
      </div>
      <div className="space-y-4 md:col-span-3">
        <div className="flex items-center gap-2"><KindBadge kind={item.kind} /><StatusBadge status={item.status} /><span className="text-xs text-slate-500">{item.category}</span></div>
        <h1 className="text-2xl font-bold">{item.title}</h1>
        <p className="whitespace-pre-wrap text-slate-300">{item.description || 'No description provided.'}</p>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div><dt className="label">Location</dt><dd>{item.location}</dd></div>
          <div><dt className="label">When</dt><dd>{new Date(item.event_time).toLocaleString()}</dd></div>
          <div><dt className="label">Posted by</dt><dd>{item.owner.name} ({item.owner.karma} karma)</dd></div>
          <div><dt className="label">Claims</dt><dd>{item.claim_count}</dd></div>
        </dl>
        {item.secret_detail && <div className="rounded-lg border border-amber-400/30 bg-amber-400/10 p-3 text-sm"><b>Secret detail (only you see this):</b> {item.secret_detail}</div>}

        {item.kind === 'found' && !mine && item.status === 'open' && (
          <form className="card space-y-3 p-4" onSubmit={(e) => { e.preventDefault(); claim.mutate() }}>
            <h2 className="font-semibold">Is this yours?</h2>
            <p className="text-sm text-slate-400">Describe a detail that isn't visible in the listing. The finder sees your answer with a similarity score.</p>
            <textarea className="input" rows={3} required minLength={5} value={answer} onChange={(e) => setAnswer(e.target.value)} />
            {claim.isError && <p className="text-sm text-rose-400">{errMsg(claim.error)}</p>}
            {claim.isSuccess && <p className="text-sm text-emerald-400">Claim sent! You'll be notified when the finder responds.</p>}
            <button className="btn" disabled={claim.isPending}>Submit claim</button>
          </form>
        )}
        {(mine || user?.role === 'admin') && <button className="btn-ghost text-rose-400" onClick={() => confirm('Delete this report?') && remove.mutate()}>Delete report</button>}
      </div>
    </div>
  )
}
