import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api'
import ItemCard from '../components/ItemCard'
import type { Item, Page } from '../types'

function useDebounced<T>(value: T, ms = 350) {
  const [v, setV] = useState(value)
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t) }, [value, ms])
  return v
}

export default function Browse() {
  const [f, setF] = useState({ q: '', kind: '', category: '', location: '', status: 'open', sort: 'newest' })
  const [page, setPage] = useState(1)
  const dq = useDebounced(f.q)
  const dl = useDebounced(f.location)
  const { data: cats = [] } = useQuery({ queryKey: ['cats'], queryFn: async () => (await api.get<string[]>('/items/meta/categories')).data })
  const { data, isFetching } = useQuery({
    queryKey: ['items', { ...f, q: dq, location: dl, page }],
    queryFn: async () => (await api.get<Page<Item>>('/items', { params: { ...f, q: dq || undefined, location: dl || undefined, kind: f.kind || undefined, category: f.category || undefined, status: f.status || undefined, page } })).data,
    placeholderData: keepPreviousData,
  })
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => { setF({ ...f, [k]: e.target.value }); setPage(1) }
  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1

  return (
    <div className="space-y-5">
      <div className="card grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-6">
        <div className="relative lg:col-span-2"><Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input className="input pl-9" placeholder="Search title or description…" value={f.q} onChange={set('q')} /></div>
        <select className="input" value={f.kind} onChange={set('kind')}><option value="">Lost &amp; found</option><option value="lost">Lost</option><option value="found">Found</option></select>
        <select className="input" value={f.category} onChange={set('category')}><option value="">All categories</option>{cats.map((c) => <option key={c}>{c}</option>)}</select>
        <input className="input" placeholder="Location" value={f.location} onChange={set('location')} />
        <select className="input" value={f.status} onChange={set('status')}><option value="open">Open</option><option value="claimed">Claimed</option><option value="returned">Returned</option><option value="">Any status</option></select>
      </div>
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>{data?.total ?? 0} results {isFetching && '· updating…'}</span>
        <select className="input w-auto" value={f.sort} onChange={set('sort')}><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{data?.items.map((i) => <ItemCard key={i.id} item={i} />)}</div>
      {data && data.total === 0 && <p className="py-16 text-center text-slate-500">Nothing matches those filters.</p>}
      <div className="flex items-center justify-center gap-3">
        <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
        <span className="text-sm text-slate-500">Page {page} of {pages}</span>
        <button className="btn-ghost" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </div>
  )
}
