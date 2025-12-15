import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '@/app/auth'
import type { ReplayResponse } from '@/app/types'
import { PokemonImage } from '@/components/pokemon/PokemonImage'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

function displayName(username: string | undefined | null) {
  if (!username) return null
  if (username === '__bot__') return 'Bot'
  return username
}

function actorLabel(actor: 'a' | 'b' | null, viewerRole: 'a' | 'b' | null, opponentLabel: string) {
  if (!actor) return '?'
  if (viewerRole) return actor === viewerRole ? 'You' : opponentLabel
  return actor === 'a' ? 'Player 1' : 'Player 2'
}

export function ReplayPage() {
  const { battleId } = useParams()
  const id = Number(battleId)
  const { apiFetch } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ReplayResponse | null>(null)
  const [finished, setFinished] = useState<boolean>(false)

  useEffect(() => {
    if (!Number.isFinite(id)) return
    let alive = true
    ;(async () => {
      setLoading(true)
        setError(null)
      try {
        const resp = await apiFetch<ReplayResponse>(`/battles/${id}/replay`)
        if (!alive) return
        setData(resp)
        setFinished(Boolean(resp.finished ?? resp.outcome))
      } catch (err) {
        if (!alive) return
        setError(err instanceof Error ? err.message : 'Failed to load replay')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [apiFetch, id])

  if (!Number.isFinite(id)) return <p className="text-sm text-destructive">Invalid battle id</p>

  const role = data?.role ?? null
  const opponentLabel = displayName(data?.opponent_username) ?? 'Opponent'

  const p1Team =
    Array.isArray(data?.p1_team_ids) && data.p1_team_ids.length
      ? data.p1_team_ids
      : typeof data?.p1_pokemon_id === 'number'
        ? [data.p1_pokemon_id]
        : []
  const p2Team =
    Array.isArray(data?.p2_team_ids) && data.p2_team_ids.length
      ? data.p2_team_ids
      : typeof data?.p2_pokemon_id === 'number'
        ? [data.p2_pokemon_id]
        : []

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Replay</h1>
          <p className="text-sm text-muted-foreground">Battle #{id}</p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/battles">Back</Link>
        </Button>
      </div>

      {loading ? <p className="text-sm text-muted-foreground">Loading…</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      {data ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2">
              <span>Seed: {data.seed}</span>
              {finished ? <Badge>finished</Badge> : <Badge variant="outline">in progress</Badge>}
            </CardTitle>
            <CardDescription>
              {data.signature ? (
                <span className="break-all">signature: {data.signature}</span>
              ) : (
                <span>Signature becomes available when battle finishes.</span>
              )}
            </CardDescription>
          </CardHeader>
           <CardContent className="space-y-4">
             {p1Team.length && p2Team.length ? (
               (() => {
                 const left =
                   role === 'b'
                     ? { team: p2Team, label: 'You' }
                     : role === 'a'
                       ? { team: p1Team, label: 'You' }
                       : { team: p1Team, label: 'Player 1' }
                 const right =
                   role === 'b'
                     ? { team: p1Team, label: opponentLabel }
                     : role === 'a'
                       ? { team: p2Team, label: opponentLabel }
                       : { team: p2Team, label: 'Player 2' }
                 return (
                   <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                     <div className="flex flex-wrap items-center gap-2">
                       <Badge variant="outline">{left.label}</Badge>
                       <div className="flex flex-wrap items-center gap-2">
                         {left.team.map((pid, idx) => (
                           <PokemonImage key={`${pid}-${idx}`} pokemonId={pid} alt={`${left.label} Pokémon #${pid}`} size={44} />
                         ))}
                       </div>
                     </div>
                     <div className="text-xs text-muted-foreground">vs</div>
                     <div className="flex flex-wrap items-center justify-end gap-2">
                       <div className="flex flex-wrap items-center gap-2">
                         {right.team.map((pid, idx) => (
                           <PokemonImage key={`${pid}-${idx}`} pokemonId={pid} alt={`${right.label} Pokémon #${pid}`} size={44} />
                         ))}
                       </div>
                       <Badge variant="outline">{right.label}</Badge>
                     </div>
                   </div>
                 )
               })()
             ) : null}
             <div className="flex items-center justify-between">
               <div className="text-sm text-muted-foreground">{data.turns.length} turn(s)</div>
              <Button
                variant="outline"
                onClick={async () => {
                  await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
                }}
              >
                Copy JSON
              </Button>
            </div>
            <Separator />
             <div className="space-y-4">
               {data.turns.map((t) => (
                 <div key={`${t.turn}-${t.rng_seed}`} className="rounded-lg border p-4">
                   <div className="flex flex-wrap items-center justify-between gap-2">
                     <div className="text-sm font-medium">
                       Round {t.turn}
                       {typeof t.phase === 'number' ? `.${t.phase + 1}` : ''}
                       {t.actor ? ` · ${actorLabel(t.actor, role, opponentLabel)}` : ''}
                     </div>
                     <div className="text-xs text-muted-foreground">initiative: {actorLabel(t.initiative, role, opponentLabel)}</div>
                   </div>
                   {t.actions ? (
                     <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-2">
                       <div>
                         <div className="text-xs text-muted-foreground">{actorLabel('a', role, opponentLabel)} action</div>
                         <pre className="mt-1 overflow-auto rounded-md bg-secondary p-3 text-xs">{JSON.stringify(t.actions.a, null, 2)}</pre>
                       </div>
                       <div>
                         <div className="text-xs text-muted-foreground">{actorLabel('b', role, opponentLabel)} action</div>
                         <pre className="mt-1 overflow-auto rounded-md bg-secondary p-3 text-xs">{JSON.stringify(t.actions.b, null, 2)}</pre>
                       </div>
                     </div>
                   ) : (
                    <div className="mt-2">
                      <div className="text-xs text-muted-foreground">Action</div>
                      <pre className="mt-1 overflow-auto rounded-md bg-secondary p-3 text-xs">{JSON.stringify(t.action, null, 2)}</pre>
                    </div>
                  )}
                  <div className="mt-3">
                    <div className="text-xs text-muted-foreground">Log</div>
                    <pre className="mt-1 overflow-auto rounded-md bg-secondary p-3 text-xs">{JSON.stringify(t.log, null, 2)}</pre>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
