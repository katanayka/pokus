import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '@/app/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>Use your Django user credentials.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={async (e) => {
              e.preventDefault()
              setError(null)
              setLoading(true)
              try {
                await login(username, password)
                navigate('/catalog')
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Login failed')
              } finally {
                setLoading(false)
              }
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input id="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <Button className="w-full" type="submit" disabled={loading || !username || !password}>
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
            <div className="text-center text-xs text-muted-foreground">
              No account?{' '}
              <Link className="underline underline-offset-4" to="/register">
                Create one
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
