export type JwtPayload = {
  user_id?: number
  username?: string
  exp?: number
}

function base64UrlToString(input: string) {
  const base64 = input.replace(/-/g, '+').replace(/_/g, '/')
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')
  return atob(padded)
}

export function decodeJwt(token: string): JwtPayload {
  const parts = token.split('.')
  if (parts.length !== 3) return {}
  try {
    const json = base64UrlToString(parts[1])
    return JSON.parse(json) as JwtPayload
  } catch {
    return {}
  }
}
