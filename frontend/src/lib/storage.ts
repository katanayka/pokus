export type Tokens = { access: string; refresh: string }

export type BattleRole = 'a' | 'b'
export type BattleSession = {
  battleId: number
  role: BattleRole
  opponentId?: number
}

const TOKENS_KEY = 'pokus.tokens'
const ACTIVE_POKEMON_KEY = 'pokus.active_pokemon_id'
const TEAM_KEY = 'pokus.team'
const BATTLE_SESSION_PREFIX = 'pokus.battle.'

export function loadTokens(): Tokens | null {
  const raw = localStorage.getItem(TOKENS_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Tokens
    if (!parsed?.access || !parsed?.refresh) return null
    return parsed
  } catch {
    return null
  }
}

export function saveTokens(tokens: Tokens) {
  localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens))
}

export function clearTokens() {
  localStorage.removeItem(TOKENS_KEY)
}

export function loadActivePokemonId(): number | null {
  const raw = localStorage.getItem(ACTIVE_POKEMON_KEY)
  if (!raw) return null
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : null
}

export function saveActivePokemonId(pokemonId: number) {
  localStorage.setItem(ACTIVE_POKEMON_KEY, String(pokemonId))
}

export function loadTeamIds(): number[] {
  const raw = localStorage.getItem(TEAM_KEY)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.map((x) => Number(x)).filter((x) => Number.isFinite(x)) as number[]
  } catch {
    return []
  }
}

export function saveTeamIds(pokemonIds: number[]) {
  const ids = (pokemonIds ?? []).map((x) => Number(x)).filter((x) => Number.isFinite(x))
  localStorage.setItem(TEAM_KEY, JSON.stringify(ids))
}

export function loadBattleSession(battleId: number): BattleSession | null {
  const raw = localStorage.getItem(`${BATTLE_SESSION_PREFIX}${battleId}`)
  if (!raw) return null
  try {
    return JSON.parse(raw) as BattleSession
  } catch {
    return null
  }
}

export function saveBattleSession(session: BattleSession) {
  localStorage.setItem(`${BATTLE_SESSION_PREFIX}${session.battleId}`, JSON.stringify(session))
}
