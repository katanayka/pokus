import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/app/auth'
import type { BattleListItem, BattleOutcome, BattleTurnRecord, Pokemon, ReplayResponse, TurnSubmitResponse } from '@/app/types'
import { PokemonImage } from '@/components/pokemon/PokemonImage'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { loadBattleSession, saveBattleSession } from '@/lib/storage'

type SideEffects = { atkMod: number; atkTurns: number; defend: number }
type SideState = { active: number | null; hp: number[]; effects: SideEffects }

type InitiativeInfo = {
  seed: number | null
  winner: 'a' | 'b' | null
  method: string | null
  aSpeed: number | null
  bSpeed: number | null
  tiebreak: number | null
}
type BattleState = {
  turn: number | null
  phase: number | null
  nextActor: 'a' | 'b' | null
  order: Array<'a' | 'b'> | null
  initiative: InitiativeInfo | null
  finished: boolean
  winner?: string
  loser?: string
  a: SideState
  b: SideState
}

function parseSideState(value: unknown): SideState {
  const v = (value ?? {}) as Record<string, unknown>
  const active = typeof v.active === 'number' ? v.active : null
  const hp = Array.isArray(v.hp) ? v.hp.map((x) => Number(x)).filter((x) => Number.isFinite(x)) : []
  const effRaw = (v.effects ?? {}) as Record<string, unknown>
  const atkMod = typeof effRaw.atk_mod === 'number' ? effRaw.atk_mod : 1
  const atkTurns = typeof effRaw.atk_turns === 'number' ? effRaw.atk_turns : 0
  const defend = typeof effRaw.defend === 'number' ? effRaw.defend : 0
  const effects: SideEffects = { atkMod, atkTurns, defend }
  return { active, hp, effects }
}

function parseInitiativeInfo(value: unknown): InitiativeInfo | null {
  if (!value || typeof value !== 'object') return null
  const initRaw = value as Record<string, unknown>
  const initiative: InitiativeInfo = {
    seed: typeof initRaw.seed === 'number' ? initRaw.seed : null,
    winner: initRaw.winner === 'a' || initRaw.winner === 'b' ? initRaw.winner : null,
    method: typeof initRaw.method === 'string' ? initRaw.method : null,
    aSpeed: typeof initRaw.a_speed === 'number' ? initRaw.a_speed : null,
    bSpeed: typeof initRaw.b_speed === 'number' ? initRaw.b_speed : null,
    tiebreak: typeof initRaw.tiebreak === 'number' ? initRaw.tiebreak : null,
  }

  if (
    initiative.seed === null &&
    initiative.winner === null &&
    initiative.method === null &&
    initiative.aSpeed === null &&
    initiative.bSpeed === null &&
    initiative.tiebreak === null
  ) {
    return null
  }
  return initiative
}

function parseBattleState(result: Record<string, unknown>): BattleState {
  const raw = (result.state ?? {}) as Record<string, unknown>

  const aRaw = raw.a
  const bRaw = raw.b
  const hasTeams = Boolean(aRaw && typeof aRaw === 'object' && bRaw && typeof bRaw === 'object')

  if (hasTeams) {
    const nextActorRaw = raw.next_actor
    const phase = typeof raw.phase === 'number' ? raw.phase : null
    let nextActor: 'a' | 'b' | null = nextActorRaw === 'a' || nextActorRaw === 'b' ? nextActorRaw : null
    const orderRaw = raw.order
    const order =
      Array.isArray(orderRaw) && orderRaw.length === 2 && orderRaw[0] !== orderRaw[1] && (orderRaw[0] === 'a' || orderRaw[0] === 'b') && (orderRaw[1] === 'a' || orderRaw[1] === 'b')
        ? (orderRaw as Array<'a' | 'b'>)
        : null
     if (!nextActor && order) {
       const idx = typeof phase === 'number' ? phase : 0
       nextActor = order[idx] ?? null
     }

     const initiative = parseInitiativeInfo(raw.initiative)
     return {
       turn: typeof raw.turn === 'number' ? raw.turn : null,
       phase,
       nextActor,
       order,
      initiative,
      finished: Boolean(raw.finished),
      winner: typeof raw.winner === 'string' ? raw.winner : undefined,
      loser: typeof raw.loser === 'string' ? raw.loser : undefined,
      a: parseSideState(aRaw),
      b: parseSideState(bRaw),
    }
  }

  // Backward compat: old 1v1 format.
  return {
    turn: typeof raw.turn === 'number' ? raw.turn : null,
    phase: null,
    nextActor: null,
    order: null,
    initiative: null,
    finished: Boolean(raw.finished),
    winner: typeof raw.winner === 'string' ? raw.winner : undefined,
    loser: typeof raw.loser === 'string' ? raw.loser : undefined,
    a: { active: 0, hp: typeof raw.p1_hp === 'number' ? [raw.p1_hp] : [], effects: { atkMod: 1, atkTurns: 0, defend: 0 } },
    b: { active: 0, hp: typeof raw.p2_hp === 'number' ? [raw.p2_hp] : [], effects: { atkMod: 1, atkTurns: 0, defend: 0 } },
  }
}

function isDrawOutcome(outcome: BattleOutcome): outcome is { draw: true; reason?: string } {
  return 'draw' in outcome && outcome.draw === true
}

function parseTeams(result: Record<string, unknown>) {
  const teams = (result.teams ?? {}) as Record<string, unknown>
  const a = Array.isArray(teams.a) ? (teams.a as Pokemon[]) : []
  const b = Array.isArray(teams.b) ? (teams.b as Pokemon[]) : []
  return { a, b }
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function hpPct(current: number | null, max: number | null) {
  if (!current || !max || max <= 0) return 0
  return clamp((current / max) * 100, 0, 100)
}

function hpColor(pct: number) {
  if (pct <= 20) return 'bg-rose-500/70'
  if (pct <= 50) return 'bg-amber-500/70'
  return 'bg-emerald-500/70'
}

function HpBar({ current, max }: { current: number | null; max: number | null }) {
  const pct = hpPct(current, max)
  return (
    <div className="h-2 w-full overflow-hidden rounded bg-secondary">
      <div className={`h-2 ${hpColor(pct)}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

function EffectsBadges({ effects }: { effects: SideEffects }) {
  const atkActive = effects.atkTurns > 0 && Math.abs(effects.atkMod - 1) > 0.001
  const defActive = effects.defend > 0
  if (!atkActive && !defActive) return <span className="text-xs text-muted-foreground">No active effects</span>

  return (
    <div className="flex flex-wrap gap-1">
      {atkActive ? (
        <Badge variant="outline">
          ATK x{effects.atkMod.toFixed(2)} ({effects.atkTurns})
        </Badge>
      ) : null}
      {defActive ? (
        <Badge variant="outline">
          DEFEND ({effects.defend})
        </Badge>
      ) : null}
    </div>
  )
}

function toFiniteNumber(value: unknown): number | null {
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : null
}

function describeAction(action: Record<string, unknown> | undefined): string | null {
  if (!action) return null
  const type = typeof action.type === 'string' ? action.type : null
  if (!type) return JSON.stringify(action)
  if (type === 'attack') {
    const attackType = typeof action.attack_type === 'string' ? action.attack_type : '?'
    return `attack (${attackType})`
  }
  if (type === 'switch') {
    const slot = toFiniteNumber(action.to ?? action.slot)
    return `switch → slot ${slot ?? '?'}`
  }
  return type
}

function describeActions(actions: unknown): string | null {
  if (!actions || typeof actions !== 'object') return null
  const v = actions as Record<string, unknown>
  const a = v.a && typeof v.a === 'object' ? describeAction(v.a as Record<string, unknown>) : null
  const b = v.b && typeof v.b === 'object' ? describeAction(v.b as Record<string, unknown>) : null
  if (a && b) return `P1: ${a} · P2: ${b}`
  return a ?? b ?? null
}

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

function TurnLogEntry({
  entry,
  viewerRole,
  opponentLabel,
}: {
  entry: Record<string, unknown>
  viewerRole: 'a' | 'b' | null
  opponentLabel: string
}) {
  const actor = entry.actor === 'a' || entry.actor === 'b' ? (entry.actor as 'a' | 'b') : null
  const action = typeof entry.action === 'string' ? entry.action : null
  const attackType = typeof entry.attack_type === 'string' ? entry.attack_type : null

  const hitRoll = toFiniteNumber(entry.hit_roll)
  const hitChance = toFiniteNumber(entry.hit_chance)
  const critRoll = toFiniteNumber(entry.crit_roll)
  const critChance = toFiniteNumber(entry.crit_chance)

  const base = toFiniteNumber(entry.base)
  const eff = toFiniteNumber(entry.effectiveness)
  const atkMod = toFiniteNumber(entry.atk_mod)
  const defendBefore = toFiniteNumber(entry.defend_before)
  const dmg = toFiniteNumber(entry.dmg)
  const crit = entry.crit === true
  const targetHp = toFiniteNumber(entry.target_hp)

  let dmgBreakdown: string | null = null
  if (base !== null && eff !== null && atkMod !== null) {
    const preCrit = Math.trunc(base * eff * atkMod)
    const postCrit = crit ? Math.trunc(preCrit * 1.5) : preCrit
    const postDefend = defendBefore !== null && defendBefore > 0 ? Math.floor(postCrit / 2) : postCrit
    const pieces = [`${base} × ${eff.toFixed(2)} × ${atkMod.toFixed(2)} = ${preCrit}`]
    if (crit) pieces.push(`crit × 1.5 = ${postCrit}`)
    if (defendBefore !== null && defendBefore > 0) pieces.push(`defend ÷ 2 = ${postDefend}`)
    dmgBreakdown = pieces.join(' · ')
  }

  if (!actor && !action) {
    return <pre className="overflow-auto rounded-md bg-secondary p-3 text-xs">{JSON.stringify(entry, null, 2)}</pre>
  }

  if (action === 'hit') {
    return (
      <div className="space-y-1 rounded-md bg-secondary/30 p-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{actorLabel(actor, viewerRole, opponentLabel)}</Badge>
          <Badge variant="outline">HIT</Badge>
          {attackType ? <span className="text-muted-foreground">{attackType}</span> : null}
          {dmg !== null ? <span className="font-medium tabular-nums text-foreground">{dmg} dmg</span> : null}
          {eff !== null ? <span className="text-muted-foreground">x{eff.toFixed(2)}</span> : null}
          {crit ? <Badge>CRIT</Badge> : null}
          {targetHp !== null ? <span className="text-muted-foreground">→ HP {targetHp}</span> : null}
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-muted-foreground">
          {hitRoll !== null && hitChance !== null ? (
            <span className="tabular-nums">
              hit {100 - hitRoll}/{100 - hitChance}
            </span>
          ) : null}
          {critRoll !== null && critChance !== null ? (
            <span className="tabular-nums">
              crit {100 - critRoll}/{100 - critChance}
            </span>
          ) : null}
          {dmgBreakdown ? <span>{dmgBreakdown}</span> : null}
        </div>
      </div>
    )
  }

  if (action === 'miss') {
    return (
      <div className="space-y-1 rounded-md bg-secondary/30 p-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{actorLabel(actor, viewerRole, opponentLabel)}</Badge>
          <Badge variant="outline">MISS</Badge>
          {attackType ? <span className="text-muted-foreground">{attackType}</span> : null}
        </div>
        {hitRoll !== null && hitChance !== null ? (
          <div className="tabular-nums text-muted-foreground">
            hit {100 - hitRoll}/{100 - hitChance}
          </div>
        ) : null}
      </div>
    )
  }

  if (action === 'switch' || action === 'autoswitch') {
    const to = toFiniteNumber(entry.to)
    const toId = toFiniteNumber(entry.to_id)
    return (
      <div className="rounded-md bg-secondary/30 p-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{actorLabel(actor, viewerRole, opponentLabel)}</Badge>
          <Badge variant="outline">{action === 'autoswitch' ? 'AUTO-SWITCH' : 'SWITCH'}</Badge>
          {to !== null ? <span className="text-muted-foreground">→ slot {to}</span> : null}
          {toId !== null ? <span className="text-muted-foreground">(# {toId})</span> : null}
        </div>
      </div>
    )
  }

  const simple = action ? action.toUpperCase() : 'LOG'
  return (
    <div className="rounded-md bg-secondary/30 p-3 text-xs">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">{actorLabel(actor, viewerRole, opponentLabel)}</Badge>
        <Badge variant="outline">{simple}</Badge>
      </div>
    </div>
  )
}

export function BattlePage() {
  const { battleId } = useParams()
  const id = Number(battleId)
  const { apiFetch } = useAuth()

  const session = useMemo(() => (Number.isFinite(id) ? loadBattleSession(id) : null), [id])
  const storedRole = session?.role ?? null

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [battle, setBattle] = useState<BattleListItem | null>(null)
  const [turns, setTurns] = useState<BattleTurnRecord[]>([])

  const [serverRole, setServerRole] = useState<'a' | 'b' | null>(null)
  const [serverOpponentId, setServerOpponentId] = useState<number | null>(null)

  const [p1TeamIds, setP1TeamIds] = useState<number[]>([])
  const [p2TeamIds, setP2TeamIds] = useState<number[]>([])

  const [fallbackTeams, setFallbackTeams] = useState<{ a: Pokemon[]; b: Pokemon[] } | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const prevSnapshotRef = useRef<{ battleId: number; step: number; nextActor: 'a' | 'b' | null } | null>(null)

  const refreshBattle = useCallback(async () => {
    const current = await apiFetch<BattleListItem>(`/battles/${id}`)
    setBattle(current ?? null)
    setServerRole(current?.role ?? null)
    setServerOpponentId(typeof current?.opponent_id === 'number' ? current.opponent_id : null)
    return current
  }, [apiFetch, id])

  const refreshReplay = useCallback(
    async (currentBattle?: BattleListItem | null) => {
      const replay = await apiFetch<ReplayResponse>(`/battles/${id}/replay`)
      setTurns(replay.turns ?? [])
      setP1TeamIds(Array.isArray(replay.p1_team_ids) ? replay.p1_team_ids : [])
      setP2TeamIds(Array.isArray(replay.p2_team_ids) ? replay.p2_team_ids : [])
      setServerRole(replay.role ?? currentBattle?.role ?? null)
      setServerOpponentId(
        typeof replay.opponent_id === 'number'
          ? replay.opponent_id
          : typeof currentBattle?.opponent_id === 'number'
            ? currentBattle.opponent_id
            : null,
      )
    },
    [apiFetch, id],
  )

  const refresh = useCallback(async () => {
    const current = await refreshBattle()
    try {
      await refreshReplay(current)
    } catch {
      // ignore (e.g., integrity check error or not found)
    }
  }, [refreshBattle, refreshReplay])

  const role = storedRole ?? serverRole
  const opponentId = session?.opponentId ?? serverOpponentId ?? null
  const opponentLabel = displayName(battle?.opponent_username) ?? 'Opponent'

  const result = (battle?.result ?? {}) as Record<string, unknown>
  const state = parseBattleState(result)

  const teamsFromResult = useMemo(() => parseTeams(result), [result])
  const teams = fallbackTeams ?? teamsFromResult

  useEffect(() => {
    if (!Number.isFinite(id)) return
    let alive = true
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        await refresh()
      } catch (err) {
        if (!alive) return
        setError(err instanceof Error ? err.message : 'Failed to load battle')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [id, refresh])

  useEffect(() => {
    if (!Number.isFinite(id)) return
    if (storedRole) return
    if (!serverRole) return
    if (loadBattleSession(id)) return
    saveBattleSession({ battleId: id, role: serverRole, opponentId: opponentId ?? undefined })
  }, [id, opponentId, serverRole, storedRole])

  useEffect(() => {
    if (!Number.isFinite(id)) return
    if (!p1TeamIds.length || !p2TeamIds.length) return
    if (teamsFromResult.a.length && teamsFromResult.b.length) {
      setFallbackTeams(null)
      return
    }

    let alive = true
    ;(async () => {
      try {
        const [a, b] = await Promise.all([
          Promise.all(p1TeamIds.map((pid) => apiFetch<Pokemon>(`/catalog/${pid}`))),
          Promise.all(p2TeamIds.map((pid) => apiFetch<Pokemon>(`/catalog/${pid}`))),
        ])
        if (!alive) return
        setFallbackTeams({ a, b })
      } catch {
        if (!alive) return
        setFallbackTeams(null)
      }
    })()
    return () => {
      alive = false
    }
  }, [apiFetch, id, p1TeamIds.join(','), p2TeamIds.join(','), teamsFromResult.a.length, teamsFromResult.b.length])

  const mySide = role === 'a' ? state.a : role === 'b' ? state.b : null
  const oppSide = role === 'a' ? state.b : role === 'b' ? state.a : null

  const myTeam = role === 'a' ? teams.a : role === 'b' ? teams.b : []
  const oppTeam = role === 'a' ? teams.b : role === 'b' ? teams.a : []

  const myActiveIdx = mySide?.active ?? 0
  const oppActiveIdx = oppSide?.active ?? 0
  const myActive = myTeam[myActiveIdx] ?? null
  const oppActive = oppTeam[oppActiveIdx] ?? null

  const myHp = typeof mySide?.hp?.[myActiveIdx] === 'number' ? mySide.hp[myActiveIdx] : null
  const oppHp = typeof oppSide?.hp?.[oppActiveIdx] === 'number' ? oppSide.hp[oppActiveIdx] : null
  const myMaxHp = typeof myActive?.stats?.hp === 'number' ? myActive.stats.hp : null
  const oppMaxHp = typeof oppActive?.stats?.hp === 'number' ? oppActive.stats.hp : null

  const availableAttackTypes = myActive?.types ?? []

  useEffect(() => {
    if (!battle || !role) return
    const round = state.turn ?? 0
    const phase = state.phase ?? 0
    const step = round * 2 + phase
    const snapshot = { battleId: battle.id, step, nextActor: state.nextActor }
    const prev = prevSnapshotRef.current
    prevSnapshotRef.current = snapshot

    if (!prev || prev.battleId !== snapshot.battleId) return
    if (state.finished || battle.status === 'finished') return
    if (snapshot.step !== prev.step && snapshot.nextActor === role) {
      toast('Your turn', { description: `Round ${round + 1}` })
    }
  }, [battle, role, state.finished, state.nextActor, state.phase, state.turn])

  useEffect(() => {
    if (!Number.isFinite(id)) return
    if (!battle) return
    if (battle.status !== 'active' || state.finished) return
    if (!role) return
    if (state.nextActor === role) return

    let alive = true
    let inFlight = false
    const pollMs = 1000

    const interval = window.setInterval(() => {
      if (!alive || inFlight) return
      inFlight = true
      ;(async () => {
        try {
          const current = await refreshBattle()
          const nextResult = (current?.result ?? {}) as Record<string, unknown>
          const nextState = parseBattleState(nextResult)
          const nextRound = nextState.turn ?? 0
          const nextPhase = nextState.phase ?? 0
          const nextStep = nextRound * 2 + nextPhase
          const shouldSyncTurns = current?.status === 'finished' || nextState.finished || nextStep !== turns.length
          if (shouldSyncTurns) await refreshReplay(current)
        } catch {
          // ignore
        } finally {
          inFlight = false
        }
      })().catch(() => undefined)
    }, pollMs)

    return () => {
      alive = false
      window.clearInterval(interval)
    }
  }, [battle, id, refreshBattle, refreshReplay, role, state.finished, state.nextActor, turns.length])

  const actionDisabled =
    submitting ||
    !role ||
    !battle ||
    battle.status !== 'active' ||
    state.finished ||
    (state.nextActor !== null && state.nextActor !== role) ||
    !myActive

  const submitAction = async (action: Record<string, unknown>) => {
    setError(null)
    setSubmitting(true)
    try {
      const resp = await apiFetch<TurnSubmitResponse>(`/battle/${id}/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action),
      })
      if (resp.status === 'resolved') {
        const phase = typeof resp.turn.phase === 'number' ? resp.turn.phase + 1 : 1
        toast('Move resolved', { description: `Round ${resp.turn.turn}.${phase}` })
      } else if (resp.status === 'finished') {
        const outcome = resp.outcome
        toast('Battle finished', {
          description: isDrawOutcome(outcome)
            ? `Draw (${outcome.reason ?? 'timeout'})`
            : outcome.winner === role
              ? 'Winner: you'
              : `Winner: ${opponentLabel}`,
        })
      }
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (!Number.isFinite(id)) return <p className="text-sm text-destructive">Invalid battle id</p>

  const switchTargets =
    mySide && myTeam.length
      ? myTeam
          .map((p, idx) => ({ pokemon: p, idx, hp: mySide.hp?.[idx] ?? null }))
          .filter((x) => x.idx !== myActiveIdx && typeof x.hp === 'number' && x.hp > 0)
      : []

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Battle</h1>
          <p className="text-sm text-muted-foreground">
            #{id} {battle ? `· ${battle.status}` : null}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => refresh().catch(() => undefined)}>
            Refresh
          </Button>
          <Button variant="outline" asChild>
            <Link to="/battles">Back</Link>
          </Button>
        </div>
      </div>

      {loading ? <p className="text-sm text-muted-foreground">Loading…</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>You</span>
            </CardTitle>
            <CardDescription>{myActive ? `#${myActive.id} ${myActive.name}` : 'Active Pokémon not loaded'}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3">
              {myActive ? <PokemonImage pokemonId={myActive.id} alt={myActive.name} size={72} /> : null}
              <div className="flex-1 space-y-2">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">HP</span>
                    <span className="font-medium tabular-nums">
                      {myHp ?? '?'} / {myMaxHp ?? '?'}
                    </span>
                  </div>
                  <HpBar current={myHp} max={myMaxHp} />
                </div>
                <div className="flex flex-wrap gap-1">
                  {(myActive?.types ?? []).map((t) => (
                    <Badge key={t} variant="outline">
                      {t}
                    </Badge>
                  ))}
                </div>
                {mySide ? (
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">Effects</div>
                    <EffectsBadges effects={mySide.effects} />
                  </div>
                ) : null}
              </div>
            </div>
            {myTeam.length ? (
              <div className="flex flex-wrap gap-2">
                {myTeam.map((p, idx) => {
                  const hp = typeof mySide?.hp?.[idx] === 'number' ? mySide.hp[idx] : null
                  const max = typeof p?.stats?.hp === 'number' ? p.stats.hp : null
                  const fainted = typeof hp === 'number' && hp <= 0
                  return (
                  <div
                    key={p.id}
                    className={`flex min-w-[220px] items-center gap-2 rounded-md border px-2 py-1 text-xs ${idx === myActiveIdx ? 'border-primary/50' : ''} ${fainted ? 'opacity-60' : ''}`}
                  >
                    <PokemonImage pokemonId={p.id} alt={p.name} size={32} />
                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate">
                          #{p.id} · {p.name}
                        </span>
                        <span className="shrink-0 tabular-nums text-muted-foreground">
                          {hp ?? '?'} / {max ?? '?'}
                        </span>
                      </div>
                      <HpBar current={hp} max={max} />
                    </div>
                  </div>
                  )
                })}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Opponent</span>
              <Badge variant="outline">{opponentLabel}</Badge>
            </CardTitle>
            <CardDescription>{oppActive ? `#${oppActive.id} ${oppActive.name}` : 'Active Pokémon not loaded'}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3">
              {oppActive ? <PokemonImage pokemonId={oppActive.id} alt={oppActive.name} size={72} /> : null}
              <div className="flex-1 space-y-2">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">HP</span>
                    <span className="font-medium tabular-nums">
                      {oppHp ?? '?'} / {oppMaxHp ?? '?'}
                    </span>
                  </div>
                  <HpBar current={oppHp} max={oppMaxHp} />
                </div>
                <div className="flex flex-wrap gap-1">
                  {(oppActive?.types ?? []).map((t) => (
                    <Badge key={t} variant="outline">
                      {t}
                    </Badge>
                  ))}
                </div>
                {oppSide ? (
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">Effects</div>
                    <EffectsBadges effects={oppSide.effects} />
                  </div>
                ) : null}
              </div>
            </div>
            {oppTeam.length ? (
              <div className="flex flex-wrap gap-2">
                {oppTeam.map((p, idx) => {
                  const hp = typeof oppSide?.hp?.[idx] === 'number' ? oppSide.hp[idx] : null
                  const max = typeof p?.stats?.hp === 'number' ? p.stats.hp : null
                  const fainted = typeof hp === 'number' && hp <= 0
                  return (
                  <div
                    key={p.id}
                    className={`flex min-w-[220px] items-center gap-2 rounded-md border px-2 py-1 text-xs ${idx === oppActiveIdx ? 'border-primary/50' : ''} ${fainted ? 'opacity-60' : ''}`}
                  >
                    <PokemonImage pokemonId={p.id} alt={p.name} size={32} />
                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate">
                          #{p.id} · {p.name}
                        </span>
                        <span className="shrink-0 tabular-nums text-muted-foreground">
                          {hp ?? '?'} / {max ?? '?'}
                        </span>
                      </div>
                      <HpBar current={hp} max={max} />
                    </div>
                  </div>
                  )
                })}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-2">
            <span>Actions</span>
            <Badge variant="outline">
              Round {typeof state.turn === 'number' ? state.turn + 1 : '?'}
              {typeof state.phase === 'number' ? `.${state.phase + 1}` : ''}
            </Badge>
            {state.order ? <Badge variant="outline">order {state.order.map((x) => actorLabel(x, role, opponentLabel)).join(' → ')}</Badge> : null}
            {state.nextActor ? <Badge>{state.nextActor === role ? 'your turn' : "opponent's turn"}</Badge> : null}
          </CardTitle>
          <CardDescription>{state.nextActor === role ? 'Your move.' : "Waiting for opponent's move."}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {state.initiative ? (
            <div className="text-xs text-muted-foreground">
              Initiative:{' '}
              <span className="font-medium">
                {state.initiative.winner ? actorLabel(state.initiative.winner, role, opponentLabel) : '?'}
              </span>{' '}
              first
              {state.initiative.method ? <span> · {state.initiative.method}</span> : null}
              {state.initiative.aSpeed !== null && state.initiative.bSpeed !== null ? (
                <span className="tabular-nums">
                  {' '}
                  {role === 'a' ? (
                    <>
                      · SPD you:{state.initiative.aSpeed} opp:{state.initiative.bSpeed}
                    </>
                  ) : role === 'b' ? (
                    <>
                      · SPD you:{state.initiative.bSpeed} opp:{state.initiative.aSpeed}
                    </>
                  ) : (
                    <>
                      · SPD p1:{state.initiative.aSpeed} p2:{state.initiative.bSpeed}
                    </>
                  )}
                </span>
              ) : null}
              {state.initiative.tiebreak !== null ? <span className="tabular-nums"> · tiebreak {state.initiative.tiebreak}</span> : null}
              {state.initiative.seed !== null ? <span className="tabular-nums"> · seed {state.initiative.seed}</span> : null}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            {availableAttackTypes.map((t) => (
              <Button key={t} disabled={actionDisabled} onClick={() => submitAction({ type: 'attack', attack_type: t })}>
                Attack ({t})
              </Button>
            ))}
            <Button variant="secondary" disabled={actionDisabled} onClick={() => submitAction({ type: 'defend' })}>
              Defend
            </Button>
            <Button variant="secondary" disabled={actionDisabled} onClick={() => submitAction({ type: 'buff' })}>
              Buff
            </Button>
            <Button variant="secondary" disabled={actionDisabled} onClick={() => submitAction({ type: 'debuff' })}>
              Debuff
            </Button>
            {switchTargets.map((x) => (
              <Button key={x.pokemon.id} variant="outline" disabled={actionDisabled} onClick={() => submitAction({ type: 'switch', slot: x.idx })}>
                Switch to {x.pokemon.name}
              </Button>
            ))}
          </div>
          <div className="text-xs text-muted-foreground">
            {!role
              ? 'Session missing.'
              : state.finished || battle?.status === 'finished'
                ? 'Finished.'
                : actionDisabled
                  ? 'Actions locked (not your turn).'
                  : 'Ready.'}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Turns</CardTitle>
          <CardDescription>Server-authoritative turn records.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {turns.length === 0 ? <p className="text-sm text-muted-foreground">No turns yet.</p> : null}
          {turns
            .slice()
            .reverse()
            .map((t) => {
              const init = parseInitiativeInfo(t.state?.initiative)
              const actionSummary = describeAction(t.action) ?? describeActions(t.actions) ?? ''
              return (
                <div key={`${t.turn}-${t.rng_seed}`} className="rounded-lg border p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="text-sm font-medium">
                      Round {t.turn}
                      {typeof t.phase === 'number' ? `.${t.phase + 1}` : ''}
                      {t.actor ? ` · ${actorLabel(t.actor, role, opponentLabel)}` : ''}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      initiative: {actorLabel(t.initiative, role, opponentLabel)}
                      {init ? (
                        <span>
                          {' '}
                          · {init.method ?? 'speed'}
                          {init.aSpeed !== null && init.bSpeed !== null ? (
                            <span className="tabular-nums">
                              {' '}
                              {role === 'a' ? (
                                <>
                                  · SPD you:{init.aSpeed} opp:{init.bSpeed}
                                </>
                              ) : role === 'b' ? (
                                <>
                                  · SPD you:{init.bSpeed} opp:{init.aSpeed}
                                </>
                              ) : (
                                <>
                                  · SPD p1:{init.aSpeed} p2:{init.bSpeed}
                                </>
                              )}
                            </span>
                          ) : null}
                          {init.tiebreak !== null ? <span className="tabular-nums"> · tiebreak {init.tiebreak}</span> : null}
                        </span>
                      ) : null}
                    </div>
                  </div>
                  <Separator className="my-3" />
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>seed</span>
                      <span className="tabular-nums">{t.rng_seed}</span>
                      {actionSummary ? (
                        <>
                          <span>·</span>
                          <span>action</span>
                          <span className="font-medium text-foreground">{actionSummary}</span>
                        </>
                      ) : null}
                    </div>

                    {Array.isArray(t.log) && t.log.length ? (
                      <div className="space-y-2">
                        {t.log.map((entry, idx) => (
                          <TurnLogEntry key={idx} entry={entry} viewerRole={role} opponentLabel={opponentLabel} />
                        ))}
                      </div>
                    ) : null}

                    <details className="rounded-md border bg-secondary/10 p-3">
                      <summary className="cursor-pointer text-xs text-muted-foreground">Raw JSON</summary>
                      <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-2">
                        <div>
                          <div className="text-xs text-muted-foreground">Action</div>
                          <pre className="mt-1 overflow-auto rounded-md bg-secondary p-3 text-xs">{JSON.stringify(t.action ?? t.actions, null, 2)}</pre>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">Log</div>
                          <pre className="mt-1 overflow-auto rounded-md bg-secondary p-3 text-xs">{JSON.stringify(t.log, null, 2)}</pre>
                        </div>
                      </div>
                    </details>
                  </div>
                </div>
              )
            })}
        </CardContent>
      </Card>
    </div>
  )
}
