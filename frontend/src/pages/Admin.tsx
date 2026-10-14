import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import type { AuditEntry, User } from '../types'

export default function Admin() {
  const qc = useQueryClient()
  const { data: users = [] } = useQuery({ queryKey: ['admin-users'], queryFn: async () => (await api.get<User[]>('/admin/users')).data })
  const { data: audit = [] } = useQuery({ queryKey: ['audit'], queryFn: async () => (await api.get<AuditEntry[]>('/admin/audit')).data })
  const toggle = useMutation({ mutationFn: async (id: number) => api.post(`/admin/users/${id}/toggle-active`), onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-users'] }); qc.invalidateQueries({ queryKey: ['audit'] }) } })
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Admin console</h1>
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase text-slate-500"><tr><th className="p-3">User</th><th>Role</th><th>Karma</th><th>Joined</th><th /></tr></thead>
          <tbody className="divide-y divide-slate-100">{users.map((u) => (
            <tr key={u.id} className={u.is_active ? '' : 'opacity-50'}><td className="p-3"><div className="font-medium">{u.name}</div><div className="text-xs text-slate-500">{u.email}</div></td><td>{u.role}</td><td>{u.karma}</td><td>{new Date(u.created_at).toLocaleDateString()}</td>
              <td className="pr-3 text-right">{u.role !== 'admin' && <button className="btn-ghost" onClick={() => toggle.mutate(u.id)}>{u.is_active ? 'Disable' : 'Enable'}</button>}</td></tr>))}</tbody></table>
      </div>
      <div className="card p-5">
        <h2 className="mb-3 font-semibold">Audit log</h2>
        <ul className="space-y-1 font-mono text-xs text-slate-600">{audit.map((a) => <li key={a.id}>{new Date(a.created_at).toLocaleString()} · user {a.actor_id ?? '-'} · <b>{a.action}</b> {a.entity}#{a.entity_id ?? '-'} {Object.keys(a.detail).length ? JSON.stringify(a.detail) : ''}</li>)}</ul>
      </div>
    </div>
  )
}
