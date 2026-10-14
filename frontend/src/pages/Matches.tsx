import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { Match } from '../types'

const Bar = ({ label, v }: { label: string; v: number }) => (
  <div className="flex items-center gap-2 text-xs"><span className="w-16 text-slate-500">{label}</span>
    <div className="h-1.5 flex-1 rounded bg-slate-100"><div className="h-1.5 rounded bg-brand-500" style={{ width: `${v * 100}%` }} /></div></div>
)

export default function Matches() {
  const { data = [], isLoading } = useQuery({ queryKey: ['matches'], queryFn: async () => (await api.get<Match[]>('/items/matches/mine')).data })
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Suggested matches</h1>
      <p className="text-sm text-slate-500">Every new report is scored against open reports of the opposite kind using text similarity, category, place and timing.</p>
      {isLoading && <p>Loading…</p>}
      {!isLoading && data.length === 0 && <p className="card p-8 text-center text-slate-500">No matches yet. We'll notify you the moment one appears.</p>}
      <div className="grid gap-4 lg:grid-cols-2">
        {data.map((m) => (
          <div key={m.id} className="card space-y-3 p-5">
            <div className="flex items-center justify-between"><span className="text-2xl font-bold text-brand-600">{Math.round(m.score * 100)}%</span><span className="text-xs text-slate-400">match</span></div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Link to={`/items/${m.lost.id}`} className="rounded-lg bg-rose-50 p-3 hover:bg-rose-100"><div className="text-xs font-semibold uppercase text-rose-700">Lost</div>{m.lost.title}<div className="text-xs text-slate-500">{m.lost.location}</div></Link>
              <Link to={`/items/${m.found.id}`} className="rounded-lg bg-teal-50 p-3 hover:bg-teal-100"><div className="text-xs font-semibold uppercase text-teal-700">Found</div>{m.found.title}<div className="text-xs text-slate-500">{m.found.location}</div></Link>
            </div>
            <div className="space-y-1"><Bar label="Text" v={m.breakdown.text} /><Bar label="Category" v={m.breakdown.category} /><Bar label="Location" v={m.breakdown.location} /><Bar label="Timing" v={m.breakdown.time} /></div>
          </div>
        ))}
      </div>
    </div>
  )
}
