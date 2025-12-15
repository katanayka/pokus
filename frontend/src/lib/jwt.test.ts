import { describe, expect, it } from 'vitest'

import { decodeJwt } from './jwt'

function b64url(value: unknown) {
  const json = JSON.stringify(value)
  const base64 = Buffer.from(json, 'utf-8').toString('base64')
  return base64.replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
}

describe('decodeJwt', () => {
  it('returns payload for valid token', () => {
    const token = `${b64url({ alg: 'none', typ: 'JWT' })}.${b64url({ user_id: 1, username: 'ash' })}.x`
    expect(decodeJwt(token)).toEqual({ user_id: 1, username: 'ash' })
  })

  it('returns empty payload for invalid token', () => {
    expect(decodeJwt('nope')).toEqual({})
  })
})
