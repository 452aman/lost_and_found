import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { PackageSearch } from 'lucide-react'
import { api, errMsg } from '../api'
import { useAuth } from '../auth'

export default function Auth({ mode }: { mode: 'login' | 'register' }) {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/" replace />

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      if (mode === 'register') await api.post('/auth/register', form)
      await login(form.email, form.password)
      navigate('/')
    } catch (err) { setError(errMsg(err)) } finally { setBusy(false) }
  }
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 to-slate-100 px-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4 p-8">
        <div className="flex items-center gap-2 text-xl font-bold text-brand-700"><PackageSearch />LostFound</div>
        <p className="text-sm text-slate-500">{mode === 'login' ? 'Sign in to find or return lost items.' : 'Create an account to start.'}</p>
        {mode === 'register' && <div><label className="label">Name</label><input className="input" required minLength={2} value={form.name} onChange={set('name')} /></div>}
        <div><label className="label">Email</label><input className="input" type="email" required value={form.email} onChange={set('email')} /></div>
        <div><label className="label">Password</label><input className="input" type="password" required minLength={mode === 'register' ? 8 : 1} value={form.password} onChange={set('password')} /></div>
        {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        <button className="btn w-full" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button>
        <p className="text-center text-sm text-slate-500">
          {mode === 'login' ? <>No account? <Link className="text-brand-600 hover:underline" to="/register">Register</Link></> : <>Have one? <Link className="text-brand-600 hover:underline" to="/login">Sign in</Link></>}
        </p>
      </form>
    </div>
  )
}
