import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/app/auth'
import type { BattleListItem } from '@/app/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

function displayName(username: string | undefined) {
  if (!username) return null
  if (username === '__bot__') return 'Bot'
  return username
}

function outcomeLabel(result: Record<string, unknown>, role: BattleListItem['role'], opponentLabel: string) {
  const outcome = result?.outcome as Record<string, unknown> | undefined
  if (!outcome) return null

  if (outcome.draw === true) {
    const reason = typeof outcome.reason === 'string' ? outcome.reason : null
    return reason ? `draw (${reason})` : 'draw'
  }

  const winner = typeof outcome.winner === 'string' ? outcome.winner : null
  const loser = typeof outcome.loser === 'string' ? outcome.loser : null
  if (!winner || !loser) return null
  if (winner === 'a' || winner === 'b') {
    if (role) return winner === role ? 'winner: you' : `winner: ${opponentLabel}`
    return winner === 'a' ? 'winner: player 1' : 'winner: player 2'
  }
  return 'winner: ?'
}

function battleSubtitle(b: BattleListItem) {
  const parts: string[] = []
  const opponentLabel = displayName(b.opponent_username) ?? 'opponent'
  parts.push(`vs ${opponentLabel}`)
  const outcome = outcomeLabel((b.result ?? {}) as Record<string, unknown>, b.role, opponentLabel)
  if (outcome) parts.push(outcome)
  return parts.length ? parts.join(' · ') : null
}

export function BattlesPage() {
  const { apiFetch } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<BattleListItem[]>([])

  useEffect(() => {
    let alive = true
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await apiFetch<BattleListItem[]>('/battles')
        if (!alive) return
        setItems(data)
      } catch (err) {
        if (!alive) return
        setError(err instanceof Error ? err.message : 'Failed to load battles')
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
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Battles</h1>
          <p className="text-sm text-muted-foreground">History and active battles.</p>
        </div>
        <Button
          variant="outline"
          onClick={async () => {
            setLoading(true)
            setError(null)
            try {
              const data = await apiFetch<BattleListItem[]>('/battles')
              setItems(data)
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to refresh')
            } finally {
              setLoading(false)
            }
          }}
        >
          Refresh
        </Button>
      </div>

      {loading ? <p className="text-sm text-muted-foreground">Loading…</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <div className="grid grid-cols-1 gap-4">
        {items.map((b) => {
          const label = battleSubtitle(b)
          return (
            <Card key={b.id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between gap-2">
                  <span>Battle #{b.id}</span>
                  <Badge variant={b.status === 'finished' ? 'outline' : 'default'}>{b.status}</Badge>
                </CardTitle>
                <CardDescription>{label ?? '—'}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center gap-2">
                {b.status !== 'finished' ? (
                  <Button asChild>
                    <Link to={`/battle/${b.id}`}>Open</Link>
                  </Button>
                ) : null}
                <Button variant="outline" asChild>
                  <Link to={`/battles/${b.id}/replay`}>Replay</Link>
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
