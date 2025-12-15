import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { X } from 'lucide-react'
import { toast } from 'sonner'

import { useAuth } from '@/app/auth'
import type { Pokemon } from '@/app/types'
import { PokemonImage } from '@/components/pokemon/PokemonImage'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { loadTeamIds, saveTeamIds } from '@/lib/storage'

function asPokemonArray(value: unknown): Pokemon[] {
  if (Array.isArray(value)) return value as Pokemon[]
  if (value && typeof value === 'object') return [value as Pokemon]
  return []
}

function move<T>(arr: T[], from: number, to: number) {
  const copy = arr.slice()
  const [item] = copy.splice(from, 1)
  copy.splice(to, 0, item)
  return copy
}

export function CatalogPage() {
  const { apiFetch } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<Pokemon[]>([])

  const [teamIds, setTeamIds] = useState<number[]>(() => loadTeamIds().slice(0, 3))
  const [savingTeam, setSavingTeam] = useState(false)
  const [serverTeam, setServerTeam] = useState<Pokemon[] | null>(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<Pokemon[] | null>(null)

  const limit = 20
  const [offset, setOffset] = useState(0)
  const [hasNext, setHasNext] = useState(true)
  const fetchDebounceMs = 200

  const safeOffset = useMemo(() => (Number.isFinite(offset) ? offset : 0), [offset])
  const page = useMemo(() => Math.floor(safeOffset / limit) + 1, [limit, safeOffset])

  useEffect(() => {
    saveTeamIds(teamIds)
  }, [teamIds])

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const team = await apiFetch<Pokemon[]>('/catalog/team')
        if (!alive) return
        setServerTeam(team)
        if (team.length) setTeamIds(team.map((p) => p.id).slice(0, 3))
      } catch {
        // ignore
      }
    })()
    return () => {
      alive = false
    }
  }, [apiFetch])

  useEffect(() => {
    const ctrl = new AbortController()
    let alive = true
    setLoading(true)
    setError(null)

    const timer = window.setTimeout(() => {
      ;(async () => {
        try {
          const data = await apiFetch<Pokemon[]>(`/catalog?limit=${limit}&offset=${safeOffset}`, { signal: ctrl.signal })
          if (!alive) return
          setItems(data)
          setHasNext(data.length >= limit)
        } catch (err) {
          if (!alive) return
          if (typeof err === "object" && err !== null && "name" in err && (err as { name: string }).name === "AbortError") return
          setError(err instanceof Error ? err.message : 'Failed to load catalog')
        } finally {
          if (alive) setLoading(false)
        }
      })().catch(() => undefined)
    }, fetchDebounceMs)
    return () => {
      alive = false
      ctrl.abort()
      window.clearTimeout(timer)
    }
  }, [apiFetch, limit, safeOffset])

  const runSearch = async () => {
    const q = searchQuery.trim()
    if (!q) return
    setSearching(true)
    setError(null)
    try {
      const raw = await apiFetch<unknown>(`/catalog/search?q=${encodeURIComponent(q)}&limit=50`)
      const results = asPokemonArray(raw).filter((p) => p && typeof p.id === 'number' && typeof p.name === 'string')
      setSearchResults(results)
      if (!results.length) toast('No matches', { description: q })
      else toast('Found', { description: `${results.length} result(s)` })
    } catch (err) {
      toast('Search failed', { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setSearching(false)
    }
  }

  const clearSearch = () => {
    setSearchResults(null)
    setSearchQuery('')
  }

  const displayItems = searchResults ?? items

  const knownById = useMemo(() => {
    const map = new Map<number, Pokemon>()
    for (const p of serverTeam ?? []) map.set(p.id, p)
    for (const p of items) map.set(p.id, p)
    for (const p of searchResults ?? []) map.set(p.id, p)
    return map
  }, [items, searchResults, serverTeam])

  const toggleTeam = (pokemonId: number) => {
    setTeamIds((prev) => {
      const already = prev.includes(pokemonId)
      if (already) return prev.filter((id) => id !== pokemonId)
      if (prev.length >= 3) return prev
      return [...prev, pokemonId]
    })
  }

  const saveTeam = async () => {
    if (teamIds.length !== 3) return
    setSavingTeam(true)
    try {
      await apiFetch('/catalog/team', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pokemon_ids: teamIds }),
      })
      toast('Team saved', { description: `#${teamIds.join(', #')}` })
    } catch (err) {
      toast('Failed to save team', { description: err instanceof Error ? err.message : String(err) })
    } finally {
      setSavingTeam(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Your catalog</h1>
          <p className="text-sm text-muted-foreground">Pick a 3-Pokémon team, then enter the lobby.</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
          <div className="flex items-center gap-2">
            <Button variant="outline" disabled={searching || !searchQuery.trim()} onClick={() => runSearch().catch(() => undefined)}>
              Search
            </Button>
            <div className="w-full sm:w-64">
              <Input
                value={searchQuery}
                placeholder="Search by id or name (e.g. 25, pikachu, saur)"
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') runSearch().catch(() => undefined)
                }}
              />
            </div>
            {searchQuery.trim() || searchResults ? (
              <Button variant="outline" onClick={clearSearch}>
                Clear
              </Button>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              disabled={Boolean(searchResults) || offset === 0}
              onClick={() => setOffset((v) => (Number.isFinite(v) ? Math.max(0, v - limit) : 0))}
            >
              Prev
            </Button>
            <div className="text-xs text-muted-foreground">{searchResults ? `${searchResults.length} results` : `Page ${page}`}</div>
            <Button
              variant="outline"
              disabled={Boolean(searchResults) || !hasNext}
              onClick={() => setOffset((v) => (Number.isFinite(v) ? v + limit : 0))}
            >
              Next
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                setLoading(true)
                setError(null)
                try {
                  const data = await apiFetch<Pokemon[]>(`/catalog?limit=${limit}&offset=${safeOffset}`)
                  setItems(data)
                  setHasNext(data.length >= limit)
                  toast('Catalog refreshed')
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Failed to refresh catalog')
                } finally {
                  setLoading(false)
                }
              }}
            >
              Refresh
            </Button>
            <Button asChild>
              <Link to="/lobby">Go to lobby</Link>
            </Button>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Team</CardTitle>
          <CardDescription>Exactly 3 Pokémon. First slot is your lead.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {[0, 1, 2].map((idx) => {
              const id = teamIds[idx] ?? null
              const p = id ? knownById.get(id) ?? null : null
              return (
                <div key={idx} className="flex items-center justify-between gap-3 rounded-lg border p-3">
                  <div className="flex min-w-0 items-center gap-3">
                    {id ? <PokemonImage pokemonId={id} alt={p?.name ?? `Pokemon #${id}`} size={44} /> : <div className="h-11 w-11 rounded-md border bg-muted" />}
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{id ? `#${id} ${p?.name ?? ''}` : `slot ${idx + 1}`}</div>
                      <div className="text-xs text-muted-foreground">{idx === 0 ? 'lead' : 'bench'}</div>
                    </div>
                  </div>
                  {id ? (
                    <div className="flex items-center gap-1">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={idx === 0}
                        onClick={() => setTeamIds((prev) => (idx > 0 ? move(prev, idx, idx - 1) : prev))}
                      >
                        Up
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={idx === teamIds.length - 1}
                        onClick={() => setTeamIds((prev) => (idx < prev.length - 1 ? move(prev, idx, idx + 1) : prev))}
                      >
                        Down
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        title="Remove from team"
                        onClick={() => setTeamIds((prev) => prev.filter((_x, i) => i !== idx))}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button disabled={savingTeam || teamIds.length !== 3} onClick={() => saveTeam().catch(() => undefined)}>
              {savingTeam ? 'Saving…' : 'Save team'}
            </Button>
            <Button variant="outline" disabled={!teamIds.length} onClick={() => setTeamIds([])}>
              Clear team
            </Button>
            <div className="text-xs text-muted-foreground">Selected: {teamIds.length}/3</div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {loading ? <p className="text-sm text-muted-foreground">Loading…</p> : null}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {displayItems.map((p) => {
          const inTeam = teamIds.includes(p.id)
          const canAdd = teamIds.length < 3
          return (
            <Card key={p.id} className={inTeam ? 'border-primary/40' : undefined}>
              <CardHeader>
                <div className="flex items-start gap-3">
                  <PokemonImage pokemonId={p.id} alt={p.name} size={64} className="shrink-0" />
                  <div className="min-w-0 flex-1">
                    <CardTitle className="flex items-center justify-between gap-2">
                      <span className="truncate">
                        #{p.id} {p.name}
                      </span>
                      {inTeam ? <Badge>team</Badge> : null}
                    </CardTitle>
                    <CardDescription className="mt-1 flex flex-wrap gap-1">
                      {p.types.map((t) => (
                        <Badge key={t} variant="outline">
                          {t}
                        </Badge>
                      ))}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-4 gap-2 text-xs text-muted-foreground">
                  <div>
                    <div className="text-[10px] uppercase tracking-wide">HP</div>
                    <div className="text-sm text-foreground">{p.stats.hp}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wide">ATK</div>
                    <div className="text-sm text-foreground">{p.stats.attack}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wide">DEF</div>
                    <div className="text-sm text-foreground">{p.stats.defense}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wide">SPD</div>
                    <div className="text-sm text-foreground">{p.stats.speed}</div>
                  </div>
                </div>

                <Button variant={inTeam ? 'secondary' : 'default'} className="w-full" disabled={!inTeam && !canAdd} onClick={() => toggleTeam(p.id)}>
                  {inTeam ? 'Remove from team' : canAdd ? 'Add to team' : 'Team is full'}
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
