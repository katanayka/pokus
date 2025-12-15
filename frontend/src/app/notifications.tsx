import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/app/auth'
import { loadBattleSession, saveBattleSession } from '@/lib/storage'

export type NotificationEvent = {
  event: string
  payload: Record<string, unknown>
  receivedAt: number
}

type NotificationsContextValue = {
  connected: boolean
  notifications: NotificationEvent[]
  last: NotificationEvent | null
}

const NotificationsContext = createContext<NotificationsContextValue | null>(null)

function wsUrl(userId: number) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const base = import.meta.env.VITE_NOTIFY_WS_URL as string | undefined
  if (base) return `${base}?user_id=${userId}`
  return `${protocol}://${window.location.host}/ws?user_id=${userId}`
}

export function NotificationsProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [connected, setConnected] = useState(false)
  const [notifications, setNotifications] = useState<NotificationEvent[]>([])

  useEffect(() => {
    if (!user?.userId) return
    const url = wsUrl(user.userId)
    const ws = new WebSocket(url)
    let alive = true

    ws.onopen = () => {
      if (!alive) return
      setConnected(true)
    }
    ws.onclose = () => {
      if (!alive) return
      setConnected(false)
    }
    ws.onerror = () => {
      if (!alive) return
      setConnected(false)
    }
    ws.onmessage = (evt) => {
      if (!alive) return
      try {
        const msg = JSON.parse(String(evt.data)) as { event?: string; payload?: Record<string, unknown> }
        if (!msg.event) return
        const next: NotificationEvent = { event: msg.event, payload: msg.payload ?? {}, receivedAt: Date.now() }
        setNotifications((prev) => [next, ...prev].slice(0, 50))

        if (msg.event === 'battle_started') {
          const battleId = Number(msg.payload?.battle_id)
          const role = String(msg.payload?.role)
          const opponentId = Number(msg.payload?.opponent_id)
          if (Number.isFinite(battleId) && (role === 'a' || role === 'b')) {
            if (!loadBattleSession(battleId)) {
              saveBattleSession({
                battleId,
                role: role as 'a' | 'b',
                opponentId: Number.isFinite(opponentId) ? opponentId : undefined,
              })
            }
            const shouldOfferOpen = window.location.pathname !== '/lobby' && window.location.pathname !== `/battle/${battleId}`
            toast('Battle started', {
              description: `Battle #${battleId}`,
              action: shouldOfferOpen
                ? {
                    label: 'Open',
                    onClick: () => navigate(`/battle/${battleId}`),
                  }
                : undefined,
            })
          } else {
            toast('Battle started', { description: `Battle #${msg.payload?.battle_id}` })
          }
        }
        else if (msg.event === 'battle_ended') toast('Battle ended', { description: `Battle #${msg.payload?.battle_id}` })
        else if (msg.event === 'victory') toast('Victory', { description: `Battle #${msg.payload?.battle_id}` })
        else if (msg.event === 'defeat') toast('Defeat', { description: `Battle #${msg.payload?.battle_id}` })
        else toast(msg.event)
      } catch {
        return
      }
    }

    return () => {
      alive = false
      setConnected(false)
      ws.close()
    }
  }, [navigate, user?.userId])

  const value = useMemo<NotificationsContextValue>(
    () => ({ connected, notifications, last: notifications[0] ?? null }),
    [connected, notifications],
  )

  return <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>
}

export function useNotifications() {
  const ctx = useContext(NotificationsContext)
  if (!ctx) throw new Error('useNotifications must be used within NotificationsProvider')
  return ctx
}
