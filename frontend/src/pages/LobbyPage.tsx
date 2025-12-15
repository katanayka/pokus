import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/app/auth'
import { useNotifications } from '@/app/notifications'
import type { CodeLobbyResponse, LobbyResponse, Pokemon } from '@/app/types'
import { PokemonImage } from '@/components/pokemon/PokemonImage'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { loadBattleSession, loadTeamIds, saveBattleSession, saveTeamIds } from '@/lib/storage'

export function LobbyPage() {
  const { apiFetch } = useAuth()
  const { last, connected } = useNotifications()
  const navigate = useNavigate()

  const [teamIds, setTeamIds] = useState<number[]>(() => loadTeamIds().slice(0, 3))
  const [team, setTeam] = useState<Pokemon[] | null>(null)
  const [status, setStatus] = useState<'idle' | 'queued' | 'matching'>('idle')
  const [error, setError] = useState<string | null>(null)
  const queueSinceRef = useRef<number | null>(null)
  const handledBattleStartedAtRef = useRef<number>(0)

  const [code, setCode] = useState('')
  const [openCode, setOpenCode] = useState<string | null>(null)
  const [queueMode, setQueueMode] = useState<'fast' | 'code' | null>(null)

  useEffect(() => {
    saveTeamIds(teamIds)
  }, [teamIds])

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const serverTeam = await apiFetch<Pokemon[]>('/catalog/team')
        if (!alive) return
        setTeam(serverTeam)
        if (serverTeam.length) setTeamIds(serverTeam.map((p) => p.id).slice(0, 3))
      } catch {
        if (alive) setTeam(null)
      }
    })()
    return () => {
      alive = false
    }
  }, [apiFetch])

  const wsBattleStarted = useMemo(() => {
    if (!last || last.event !== 'battle_started') return null
    const battleId = Number(last.payload?.battle_id)
    const role = String(last.payload?.role)
    const opponentId = Number(last.payload?.opponent_id)
    if (!Number.isFinite(battleId) || (role !== 'a' && role !== 'b')) return null
    return {
      battleId,
      role: role as 'a' | 'b',
      opponentId: Number.isFinite(opponentId) ? opponentId : undefined,
      receivedAt: last.receivedAt,
    }
  }, [last])

  useEffect(() => {
    if (status !== 'queued') return
    if (!wsBattleStarted) return
    const queueSince = queueSinceRef.current
    if (typeof queueSince === 'number' && wsBattleStarted.receivedAt < queueSince) return
    if (wsBattleStarted.receivedAt <= handledBattleStartedAtRef.current) return
    handledBattleStartedAtRef.current = wsBattleStarted.receivedAt
    if (!loadBattleSession(wsBattleStarted.battleId)) {
      saveBattleSession({ battleId: wsBattleStarted.battleId, role: wsBattleStarted.role, opponentId: wsBattleStarted.opponentId })
    }
    navigate(`/battle/${wsBattleStarted.battleId}`)
  }, [navigate, status, wsBattleStarted])

  const ready = teamIds.length === 3
  const codeReady = code.length === 4
  const busy = status === 'matching' || status === 'queued'

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Lobby</h1>
          <p className="text-sm text-muted-foreground">Enter matchmaking and wait for a battle.</p>
        </div>
        <div className="text-xs text-muted-foreground">{connected ? 'Notifications: connected' : 'Notifications: offline'}</div>
      </div>

        {!ready ? (
        <Card>
          <CardHeader>
            <CardTitle>No active team</CardTitle>
            <CardDescription>Select exactly 3 Pokémon in your catalog.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link to="/catalog">Go to catalog</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
          <Card>
            <CardHeader>
              <CardTitle>Ready</CardTitle>
              <CardDescription>Your team (lead is first)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              {teamIds.map((id, idx) => (
                <div key={id} className="flex items-center gap-2 rounded-lg border px-3 py-2">
                  <PokemonImage pokemonId={id} alt={`Pokemon #${id}`} size={44} />
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">#{id}</div>
                    <div className="text-xs text-muted-foreground">{idx === 0 ? 'lead' : 'bench'}</div>
                  </div>
                </div>
              ))}
            </div>

              {team?.length ? (
                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                {team.map((p) => (
                  <span key={p.id} className="inline-flex items-center gap-1">
                    #{p.id} {p.name}
                    {p.types.map((t) => (
                      <Badge key={`${p.id}-${t}`} variant="outline">
                        {t}
                      </Badge>
                    ))}
                  </span>
                ))}
                </div>
              ) : null}

              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="space-y-3 rounded-lg border p-3">
                  <div>
                    <div className="text-sm font-medium">Fast battle</div>
                    <div className="text-xs text-muted-foreground">Auto matchmaking.</div>
                  </div>
                  <Button
                    className="w-full"
                    disabled={busy}
                    onClick={async () => {
                      setError(null)
                      setStatus('matching')
                      setQueueMode('fast')
                      setOpenCode(null)
                      queueSinceRef.current = Date.now()
                      try {
                        const res = await apiFetch<LobbyResponse>('/lobby', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ pokemon_ids: teamIds }),
                        })
                        if (res.status === 'matched') {
                          saveBattleSession({ battleId: res.battle_id, role: 'b', opponentId: res.opponent_id })
                          navigate(`/battle/${res.battle_id}`)
                          return
                        }
                        setStatus('queued')
                        toast('Queued', { description: 'Waiting for opponent...' })
                      } catch (err) {
                        setStatus('idle')
                        setQueueMode(null)
                        setError(err instanceof Error ? err.message : 'Failed to find a match.')
                      }
                    }}
                  >
                    {status === 'matching' && queueMode === 'fast' ? 'Entering…' : status === 'queued' && queueMode === 'fast' ? 'Queued' : 'Fast battle'}
                  </Button>
                </div>

                <div className="space-y-3 rounded-lg border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium">Private lobby</div>
                      <div className="text-xs text-muted-foreground">4-digit code to create/join.</div>
                    </div>
                    {openCode ? <Badge variant="outline">code {openCode}</Badge> : null}
                  </div>

                  <div className="flex items-end gap-2">
                    <div className="min-w-0 flex-1 space-y-2">
                      <Label htmlFor="lobby-code">Code</Label>
                      <Input
                        id="lobby-code"
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        placeholder="0000"
                        maxLength={4}
                        value={code}
                        onChange={(e) => {
                          const next = e.target.value.replace(/\\D/g, '').slice(0, 4)
                          setCode(next)
                        }}
                      />
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      disabled={busy}
                      onClick={() => {
                        const next = String(Math.floor(Math.random() * 10000)).padStart(4, '0')
                        setCode(next)
                      }}
                    >
                      Generate
                    </Button>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      disabled={busy || !codeReady}
                      onClick={async () => {
                        setError(null)
                        setStatus('matching')
                        setQueueMode('code')
                        setOpenCode(null)
                        queueSinceRef.current = Date.now()
                        try {
                          const res = await apiFetch<CodeLobbyResponse>('/lobby/code', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ code, pokemon_ids: teamIds }),
                          })
                          if (res.status === 'matched') {
                            saveBattleSession({ battleId: res.battle_id, role: 'b', opponentId: res.opponent_id })
                            navigate(`/battle/${res.battle_id}`)
                            return
                          }
                          setOpenCode(res.code)
                          setStatus('queued')
                          toast('Lobby open', { description: `Code ${res.code}` })
                        } catch (err) {
                          setStatus('idle')
                          setQueueMode(null)
                          setError(err instanceof Error ? err.message : 'Failed to open/join lobby.')
                        }
                      }}
                    >
                      {status === 'matching' && queueMode === 'code'
                        ? 'Opening…'
                        : status === 'queued' && queueMode === 'code'
                          ? 'Waiting…'
                          : 'Join / Create'}
                    </Button>

                    {status === 'queued' && queueMode === 'code' && openCode ? (
                      <Button
                        variant="outline"
                        onClick={async () => {
                          setError(null)
                          try {
                            await apiFetch<{ status: string }>('/lobby/code/close', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ code: openCode }),
                            })
                            setStatus('idle')
                            setQueueMode(null)
                            setOpenCode(null)
                            toast('Lobby closed')
                          } catch (err) {
                            setError(err instanceof Error ? err.message : 'Failed to close lobby.')
                          }
                        }}
                      >
                        Close
                      </Button>
                    ) : null}
                  </div>

                  {status === 'queued' && queueMode === 'code' && openCode ? (
                    <div className="text-xs text-muted-foreground">Share the code and wait for your opponent.</div>
                  ) : null}
                </div>
              </div>

              <Separator />

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant="secondary"
                  disabled={busy}
                  onClick={async () => {
                    setError(null)
                    setStatus('matching')
                    setQueueMode(null)
                    setOpenCode(null)
                    try {
                      const res = await apiFetch<LobbyResponse>('/battle/pve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ pokemon_ids: teamIds }),
                      })
                      if (res.status !== 'matched') throw new Error('Unexpected response')
                      saveBattleSession({ battleId: res.battle_id, role: 'b', opponentId: res.opponent_id })
                      navigate(`/battle/${res.battle_id}`)
                    } catch (err) {
                      setStatus('idle')
                      setError(err instanceof Error ? err.message : 'Failed to start PVE battle.')
                    }
                  }}
                >
                  Play vs bot
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/battles">Battle history</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/catalog">Edit team</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  )
}
