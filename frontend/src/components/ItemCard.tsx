import { MapPin, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Item, ItemStatus } from '../types'

const statusCls: Record<ItemStatus, string> = {
  open: 'bg-emerald-50 text-emerald-700', matched: 'bg-amber-50 text-amber-700',
  claimed: 'bg-sky-50 text-sky-700', returned: 'bg-violet-50 text-violet-700', archived: 'bg-slate-100 text-slate-500',
}

export const StatusBadge = ({ status }: { status: ItemStatus }) => (
  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusCls[status]}`}>{status}</span>
)

export const KindBadge = ({ kind }: { kind: Item['kind'] }) => (
  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${kind === 'lost' ? 'bg-rose-50 text-rose-700' : 'bg-teal-50 text-teal-700'}`}>{kind}</span>
)

export default function ItemCard({ item }: { item: Item }) {
  return (
    <Link to={`/items/${item.id}`} className="card group overflow-hidden transition hover:shadow-md">
      <div className="flex h-36 items-center justify-center bg-slate-100">
        {item.image_url
          ? <img src={item.image_url} alt={item.title} className="h-full w-full object-cover transition group-hover:scale-105" />
          : <span className="text-4xl">{item.kind === 'lost' ? '🔍' : '📦'}</span>}
      </div>
      <div className="space-y-2 p-4">
        <div className="flex items-center justify-between"><KindBadge kind={item.kind} /><StatusBadge status={item.status} /></div>
        <h3 className="line-clamp-1 font-semibold">{item.title}</h3>
        <p className="line-clamp-2 min-h-10 text-sm text-slate-500">{item.description || 'No description'}</p>
        <div className="flex flex-col gap-1 text-xs text-slate-500">
          <span className="flex items-center gap-1"><MapPin size={12} />{item.location}</span>
          <span className="flex items-center gap-1"><Clock size={12} />{new Date(item.event_time).toLocaleString()}</span>
        </div>
      </div>
    </Link>
  )
}
