export type PokemonStats = {
  hp: number
  attack: number
  defense: number
  speed: number
}

export type Pokemon = {
  id: number
  name: string
  types: string[]
  stats: PokemonStats
}

export type BattleListItem = {
  id: number
  status: string
  result: Record<string, unknown>
  role?: 'a' | 'b'
  opponent_id?: number
  opponent_username?: string
  created_at?: string
}

export type UserStats = {
  wins: number
  losses: number
  draws: number
  battles_total: number
  damage: number
  crits: number
  win_rate: number
  top_pokemons: Array<{
    pokemon_id: number
    name?: string
    battles: number
    wins: number
    losses: number
    draws: number
    win_rate: number
  }>
  daily: Array<{ date: string; battles: number; wins: number; losses: number; draws: number }>
}

export type LobbyResponse =
  | { status: 'queued' }
  | { status: 'matched'; battle_id: number; opponent_id: number }

export type CodeLobbyResponse =
  | { status: 'open'; code: string }
  | { status: 'matched'; battle_id: number; opponent_id: number }

export type BattleOutcome =
  | { winner: 'a' | 'b'; loser: 'a' | 'b' }
  | { draw: true; reason?: string }

export type BattleTurnRecord = {
  turn: number
  rng_seed: number
  initiative: 'a' | 'b'
  phase?: number
  actor?: 'a' | 'b'
  action?: Record<string, unknown>
  actions?: { a: Record<string, unknown>; b: Record<string, unknown> }
  log: Array<Record<string, unknown>>
  state: Record<string, unknown>
}

export type TurnSubmitResponse =
  | { status: 'resolved'; turn: BattleTurnRecord }
  | { status: 'finished'; turn?: BattleTurnRecord; outcome: BattleOutcome }

export type ReplayResponse = {
  battle_id: number
  seed: number
  finished?: boolean
  role?: 'a' | 'b'
  opponent_id?: number
  opponent_username?: string
  p1_pokemon_id?: number
  p2_pokemon_id?: number
  p1_team_ids?: number[]
  p2_team_ids?: number[]
  type_chart?: Record<string, Record<string, number>>
  turns: BattleTurnRecord[]
  outcome?: BattleOutcome
  signature?: string
}
