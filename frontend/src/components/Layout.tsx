import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, LayoutDashboard, LogOut, PackageSearch, PlusCircle, ShieldCheck, Sparkles, Inbox } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api, tokens } from '../api'
import { useAuth } from '../auth'
import type { Notification } from '../types'

const navCls = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'}`

function Bell_() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const { data: count = 0 } = useQuery({ queryKey: ['unread'], queryFn: async () => (await api.get('/notifications/unread-count')).data.count })
  const { data: list = [] } = useQuery({ queryKey: ['notifications'], queryFn: async () => (await api.get<Notification[]>('/notifications')).data, enabled: open })

  // Live push over WebSocket; reconnects with backoff if the socket drops.
  useEffect(() => {
    let ws: WebSocket | null = null
    let retry = 1000
    let stopped = false
    const connect = () => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${location.host}/api/v1/ws/notifications?token=${tokens.access}`)
      ws.onmessage = (e) => {
        setToast(JSON.parse(e.data).message)
        setTimeout(() => setToast(null), 4000)
        qc.invalidateQueries({ queryKey: ['unread'] })
        qc.invalidateQueries({ queryKey: ['notifications'] })
        qc.invalidateQueries({ queryKey: ['matches'] })
        qc.invalidateQueries({ queryKey: ['claims'] })
      }
      ws.onopen = () => { retry = 1000 }
      ws.onclose = () => { if (!stopped) setTimeout(connect, (retry = Math.min(retry * 2, 15000))) }
    }
    connect()
    const ping = setInterval(() => ws?.readyState === 1 && ws.send('ping'), 25000)
    return () => { stopped = true; clearInterval(ping); ws?.close() }
  }, [qc])

  const readAll = async () => {
    await api.post('/notifications/read-all')
    qc.invalidateQueries({ queryKey: ['unread'] })
    qc.invalidateQueries({ queryKey: ['notifications'] })
  }

  return (
    <div className="relative">
      <button className="relative rounded-lg p-2 hover:bg-slate-100" onClick={() => setOpen(!open)} aria-label="Notifications">
        <Bell size={20} />
        {count > 0 && <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">{count}</span>}
      </button>
      {open && (
        <div className="card absolute right-0 z-20 mt-2 w-80 overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2">
            <span className="text-sm font-semibold">Notifications</span>
            <button className="text-xs text-brand-600 hover:underline" onClick={readAll}>Mark all read</button>
          </div>
          <ul className="max-h-80 divide-y divide-slate-100 overflow-y-auto">
            {list.length === 0 && <li className="p-4 text-sm text-slate-500">Nothing yet.</li>}
            {list.map((n) => (
              <li key={n.id}>
                <button onClick={() => { setOpen(false); if (n.link) navigate(n.link) }}
                  className={`w-full px-4 py-3 text-left text-sm hover:bg-slate-50 ${n.read ? 'text-slate-500' : 'font-medium'}`}>
                  {n.message}
                  <div className="mt-0.5 text-xs font-normal text-slate-400">{new Date(n.created_at).toLocaleString()}</div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {toast && <div className="fixed bottom-6 right-6 z-50 max-w-sm rounded-xl bg-slate-900 px-4 py-3 text-sm text-white shadow-lg">{toast}</div>}
    </div>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold text-brand-700"><PackageSearch /> LostFound</Link>
          <nav className="ml-4 hidden gap-1 md:flex">
            <NavLink to="/" end className={navCls}><LayoutDashboard size={16} />Dashboard</NavLink>
            <NavLink to="/browse" className={navCls}><PackageSearch size={16} />Browse</NavLink>
            <NavLink to="/matches" className={navCls}><Sparkles size={16} />My matches</NavLink>
            <NavLink to="/claims" className={navCls}><Inbox size={16} />Claims</NavLink>
            {user?.role === 'admin' && <NavLink to="/admin" className={navCls}><ShieldCheck size={16} />Admin</NavLink>}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <Link to="/report" className="btn"><PlusCircle size={16} />Report item</Link>
            <Bell_ />
            <span className="hidden text-sm text-slate-600 sm:block">{user?.name} · {user?.karma} karma</span>
            <button className="rounded-lg p-2 hover:bg-slate-100" onClick={logout} aria-label="Log out"><LogOut size={18} /></button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6"><Outlet /></main>
    </div>
  )
}
