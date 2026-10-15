import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import type { Stats, UserPublic } from '../types'

const COLORS = ['#6366f1', '#14b8a6', '#f59e0b', '#f43f5e', '#0ea5e9', '#8b5cf6', '#84cc16', '#64748b']

const Tile = ({ label, value, hint }: { label: string; value: string | number; hint?: string }) => (
  <div className="card p-5"><div className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</div>
    <div className="mt-1 text-3xl font-bold">{value}</div>{hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}</div>
)

export default function Dashboard() {
  const { data: s } = useQuery({ queryKey: ['stats'], queryFn: async () => (await api.get<Stats>('/stats')).data })
  const { data: board = [] } = useQuery({ queryKey: ['board'], queryFn: async () => (await api.get<UserPublic[]>('/leaderboard')).data })
  if (!s) return <p className="text-slate-400">Loading…</p>
  const cats = Object.entries(s.by_category).map(([name, value]) => ({ name, value }))
  const locs = Object.entries(s.by_location).map(([name, count]) => ({ name, count }))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Campus overview</h1>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Tile label="Total reports" value={s.total_items} />
        <Tile label="Open lost" value={s.open_lost} />
        <Tile label="Open found" value={s.open_found} />
        <Tile label="Returned" value={s.returned} hint={`${Math.round(s.return_rate * 100)}% return rate`} />
        <Tile label="Pending claims" value={s.pending_claims} />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <h2 className="mb-3 font-semibold">Reports, last 14 days</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={s.daily}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.10)" /><XAxis dataKey="date" tickFormatter={(d) => d.slice(5)} fontSize={12} /><YAxis allowDecimals={false} fontSize={12} /><Tooltip />
              <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} dot={false} /></LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-5">
          <h2 className="mb-3 font-semibold">By category</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart><Pie data={cats} dataKey="value" nameKey="name" innerRadius={50} outerRadius={85}>{cats.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-5 lg:col-span-2">
          <h2 className="mb-3 font-semibold">Hotspots: where things go missing</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={locs} layout="vertical" margin={{ left: 30 }}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.10)" /><XAxis type="number" allowDecimals={false} fontSize={12} /><YAxis type="category" dataKey="name" width={110} fontSize={12} /><Tooltip /><Bar dataKey="count" fill="#14b8a6" radius={[0, 4, 4, 0]} /></BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-5">
          <h2 className="mb-3 font-semibold">Top finders 🏆</h2>
          <ol className="space-y-2">{board.length === 0 && <li className="text-sm text-slate-400">No returns yet.</li>}
            {board.map((u, i) => <li key={u.id} className="flex justify-between text-sm"><span>{i + 1}. {u.name}</span><span className="font-semibold text-brand-600">{u.karma}</span></li>)}</ol>
        </div>
      </div>
    </div>
  )
}
