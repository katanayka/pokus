import { useEffect, useState } from 'react'

import { useAuth } from '@/app/auth'
import type { UserStats } from '@/app/types'
import { PokemonImage } from '@/components/pokemon/PokemonImage'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function RecentActivityChart({ daily }: { daily: UserStats['daily'] }) {
  if (!daily.length) return <p className="text-sm text-muted-foreground">No recent activity.</p>
  const maxBattles = Math.max(1, ...daily.map((d) => d.battles))
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-sm bg-emerald-500/60" />
          wins
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-sm bg-rose-500/60" />
          losses
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-sm bg-muted-foreground/30" />
          draws
        </span>
      </div>

      <div className="flex items-end gap-1">
        {daily.map((d, idx) => {
          const winsH = (d.wins / maxBattles) * 100
          const lossesH = (d.losses / maxBattles) * 100
          const drawsH = (d.draws / maxBattles) * 100
          const label = idx === 0 || idx === daily.length - 1
          return (
            <div key={d.date} className="flex flex-col items-center gap-1">
              <div
                className="flex h-20 w-3 flex-col justify-end overflow-hidden rounded bg-secondary"
                title={`${d.date}: ${d.battles} battle(s) • ${d.wins}W ${d.losses}L ${d.draws}D`}
              >
                {d.draws ? <div className="bg-muted-foreground/30" style={{ height: `${clamp(drawsH, 0, 100)}%` }} /> : null}
                {d.losses ? <div className="bg-rose-500/60" style={{ height: `${clamp(lossesH, 0, 100)}%` }} /> : null}
                {d.wins ? <div className="bg-emerald-500/60" style={{ height: `${clamp(winsH, 0, 100)}%` }} /> : null}
              </div>
              <div className="h-3 text-[10px] text-muted-foreground">{label ? d.date.slice(5) : null}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function TopPokemons({ items }: { items: UserStats['top_pokemons'] }) {
  if (!items.length) return <p className="text-sm text-muted-foreground">No finished battles yet.</p>
  return (
    <div className="space-y-3">
      {items.map((p) => (
        <div key={p.pokemon_id} className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <PokemonImage pokemonId={p.pokemon_id} alt={p.name ?? `Pokemon #${p.pokemon_id}`} size={44} />
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">
                #{p.pokemon_id} {p.name ?? 'unknown'}
              </div>
              <div className="text-xs text-muted-foreground">
                {p.battles} battle(s) • {p.wins}W {p.losses}L {p.draws}D
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium">{p.win_rate.toFixed(1)}%</div>
            <div className="mt-1 h-1.5 w-28 overflow-hidden rounded bg-secondary">
              <div className="h-full rounded bg-primary" style={{ width: `${clamp(p.win_rate, 0, 100)}%` }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function StatsPage() {
  const { apiFetch } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<UserStats | null>(null)

  useEffect(() => {
    let alive = true
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await apiFetch<UserStats>('/stats/me')
        if (!alive) return
        setStats(data)
      } catch (err) {
        if (!alive) return
        setError(err instanceof Error ? err.message : 'Failed to load stats')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [apiFetch])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Statistics</h1>
        <p className="text-sm text-muted-foreground">Aggregated results from finished battles.</p>
      </div>

      {loading ? <p className="text-sm text-muted-foreground">Loading…</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      {stats ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Record</CardTitle>
                <CardDescription>W / L / D</CardDescription>
              </CardHeader>
              <CardContent className="text-3xl font-semibold tracking-tight">
                {stats.wins} – {stats.losses} – {stats.draws}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Win rate</CardTitle>
                <CardDescription>Percent</CardDescription>
              </CardHeader>
              <CardContent className="text-3xl font-semibold tracking-tight">{stats.win_rate.toFixed(2)}%</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Total battles</CardTitle>
                <CardDescription>Finished</CardDescription>
              </CardHeader>
              <CardContent className="text-3xl font-semibold tracking-tight">{stats.battles_total}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Damage</CardTitle>
                <CardDescription>Total dealt</CardDescription>
              </CardHeader>
              <CardContent className="text-3xl font-semibold tracking-tight">{stats.damage}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Critical hits</CardTitle>
                <CardDescription>Total</CardDescription>
              </CardHeader>
              <CardContent className="text-3xl font-semibold tracking-tight">{stats.crits}</CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Top Pokémon</CardTitle>
                <CardDescription>Most played in finished battles</CardDescription>
              </CardHeader>
              <CardContent>
                <TopPokemons items={stats.top_pokemons} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Last 14 days</CardTitle>
                <CardDescription>Finished battles per day</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <RecentActivityChart daily={stats.daily} />
                <Separator />
                <div className="text-xs text-muted-foreground">Tip: hover bars to see exact counts.</div>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  )
}
