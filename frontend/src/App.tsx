import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import Admin from './pages/Admin'
import Auth from './pages/Auth'
import Browse from './pages/Browse'
import Claims from './pages/Claims'
import Dashboard from './pages/Dashboard'
import ItemDetail from './pages/ItemDetail'
import Matches from './pages/Matches'
import Report from './pages/Report'

function Protected({ admin = false }: { admin?: boolean }) {
  const { user, loading } = useAuth()
  if (loading) return <p className="p-8 text-slate-400">Loading…</p>
  if (!user) return <Navigate to="/login" replace />
  if (admin && user.role !== 'admin') return <Navigate to="/" replace />
  return <Layout />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth mode="login" />} />
      <Route path="/register" element={<Auth mode="register" />} />
      <Route element={<Protected />}>
        <Route index element={<Dashboard />} />
        <Route path="browse" element={<Browse />} />
        <Route path="report" element={<Report />} />
        <Route path="items/:id" element={<ItemDetail />} />
        <Route path="matches" element={<Matches />} />
        <Route path="claims" element={<Claims />} />
        <Route path="claims/incoming" element={<Claims />} />
        <Route path="claims/mine" element={<Claims />} />
      </Route>
      <Route element={<Protected admin />}><Route path="admin" element={<Admin />} /></Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
