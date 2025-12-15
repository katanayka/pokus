import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from '@/app/auth'
import { AppShell } from '@/components/layout/AppShell'
import { BattlePage } from '@/pages/BattlePage'
import { BattlesPage } from '@/pages/BattlesPage'
import { CatalogPage } from '@/pages/CatalogPage'
import { LobbyPage } from '@/pages/LobbyPage'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { ReplayPage } from '@/pages/ReplayPage'
import { StatsPage } from '@/pages/StatsPage'

function RequireAuth({ children }: { children: ReactNode }) {
  const { tokens } = useAuth()
  if (!tokens?.access) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/catalog" replace />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/lobby" element={<LobbyPage />} />
        <Route path="/battle/:battleId" element={<BattlePage />} />
        <Route path="/battles" element={<BattlesPage />} />
        <Route path="/battles/:battleId/replay" element={<ReplayPage />} />
        <Route path="/stats" element={<StatsPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
