import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api'
import type { Claim } from '../types'

const badge: Record<string, string> = { pending: 'bg-amber-50 text-amber-700', approved: 'bg-emerald-50 text-emerald-700', rejected: 'bg-rose-50 text-rose-700', expired: 'bg-slate-100 text-slate-500' }

function ClaimRow({ c, reviewer }: { c: Claim; reviewer: boolean }) {
  const qc = useQueryClient()
  const refresh = () => { qc.invalidateQueries({ queryKey: ['claims'] }); qc.invalidateQueries({ queryKey: ['me'] }); qc.invalidateQueries({ queryKey: ['stats'] }) }
  const decide = useMutation({ mutationFn: async (approve: boolean) => api.post(`/claims/${c.id}/decision`, { approve }), onSuccess: refresh })
  const returned = useMutation({ mutationFn: async () => api.post(`/claims/${c.id}/returned`), onSuccess: refresh })
  const strong = c.verification_score >= 0.5
  return (
    <div className="card space-y-3 p-5">
      <div className="flex items-center justify-between"><h3 className="font-semibold">{c.item_title}</h3><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge[c.status]}`}>{c.status}</span></div>
      <p className="rounded-lg bg-slate-50 p-3 text-sm">“{c.answer}”</p>
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>{reviewer ? `by ${c.claimant.name}` : new Date(c.created_at).toLocaleDateString()}</span>
        <span className={strong ? 'font-semibold text-emerald-600' : 'font-semibold text-amber-600'}>Verification {Math.round(c.verification_score * 100)}% · {strong ? 'strong' : 'weak'}</span>
      </div>
      {reviewer && c.status === 'pending' && (
        <div className="flex gap-2"><button className="btn" onClick={() => decide.mutate(true)}>Approve</button><button className="btn-ghost" onClick={() => decide.mutate(false)}>Reject</button></div>
      )}
      {reviewer && c.status === 'approved' && <button className="btn" onClick={() => returned.mutate()}>Mark as returned (+10 karma)</button>}
    </div>
  )
}

export default function Claims() {
  const [tab, setTab] = useState<'incoming' | 'mine'>('incoming')
  const { data = [], isLoading } = useQuery({ queryKey: ['claims', tab], queryFn: async () => (await api.get<Claim[]>(`/claims/${tab}`)).data })
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Claims</h1>
      <div className="inline-flex rounded-lg bg-slate-100 p-1 text-sm">
        {(['incoming', 'mine'] as const).map((t) => <button key={t} onClick={() => setTab(t)} className={`rounded-md px-4 py-1.5 font-medium ${tab === t ? 'bg-white shadow-sm' : 'text-slate-500'}`}>{t === 'incoming' ? 'On items I found' : 'My claims'}</button>)}
      </div>
      {isLoading && <p>Loading…</p>}
      {!isLoading && data.length === 0 && <p className="card p-8 text-center text-slate-500">Nothing here yet.</p>}
      <div className="grid gap-4 lg:grid-cols-2">{data.map((c) => <ClaimRow key={c.id} c={c} reviewer={tab === 'incoming'} />)}</div>
    </div>
  )
}
