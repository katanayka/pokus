import { Link, NavLink, Outlet } from 'react-router-dom'
import { LogOut, Swords, UserRound } from 'lucide-react'

import { useAuth } from '@/app/auth'
import { useNotifications } from '@/app/notifications'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/catalog', label: 'Catalog' },
  { to: '/lobby', label: 'Lobby' },
  { to: '/battles', label: 'Battles' },
  { to: '/stats', label: 'Stats' },
]

export function AppShell() {
  const { user, logout } = useAuth()
  const { connected } = useNotifications()

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4">
          <Link to="/catalog" className="inline-flex items-center gap-2 text-sm font-semibold tracking-tight">
            <Swords className="h-4 w-4" />
            Pokus
          </Link>

          <nav className="hidden items-center gap-2 sm:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    'rounded-md px-3 py-2 text-sm text-muted-foreground hover:text-foreground',
                    isActive && 'bg-secondary text-foreground',
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <div className="hidden items-center gap-2 text-xs text-muted-foreground md:flex">
              <span className={cn('h-2 w-2 rounded-full', connected ? 'bg-emerald-500' : 'bg-zinc-500')} />
              <span>{connected ? 'notify: connected' : 'notify: offline'}</span>
            </div>
            <div className="hidden items-center gap-2 rounded-md border px-3 py-2 text-xs text-muted-foreground sm:flex">
              <UserRound className="h-4 w-4" />
              <span>{user?.username ?? `user#${user?.userId ?? '-'}`}</span>
            </div>
            <Button variant="outline" size="sm" onClick={logout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
