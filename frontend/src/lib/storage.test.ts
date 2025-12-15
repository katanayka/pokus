import { describe, expect, it } from 'vitest'

import {
  clearTokens,
  loadActivePokemonId,
  loadBattleSession,
  loadTeamIds,
  loadTokens,
  saveActivePokemonId,
  saveBattleSession,
  saveTeamIds,
  saveTokens,
} from './storage'

describe('storage', () => {
  it('roundtrips tokens', () => {
    expect(loadTokens()).toBeNull()
    saveTokens({ access: 'a', refresh: 'r' })
    expect(loadTokens()).toEqual({ access: 'a', refresh: 'r' })
    clearTokens()
    expect(loadTokens()).toBeNull()
  })

  it('roundtrips active pokemon id', () => {
    expect(loadActivePokemonId()).toBeNull()
    saveActivePokemonId(25)
    expect(loadActivePokemonId()).toBe(25)
  })

  it('filters team ids on save/load', () => {
    saveTeamIds([1, 2, Number.NaN, 3])
    expect(loadTeamIds()).toEqual([1, 2, 3])
  })

  it('roundtrips battle session', () => {
    expect(loadBattleSession(1)).toBeNull()
    saveBattleSession({ battleId: 1, role: 'a', opponentId: 2 })
    expect(loadBattleSession(1)).toEqual({ battleId: 1, role: 'a', opponentId: 2 })
  })
})
