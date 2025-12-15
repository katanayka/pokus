import { useMemo, useState } from 'react'

import { pokemonArtworkUrl, pokemonSpriteUrl } from '@/lib/pokemon'
import { cn } from '@/lib/utils'

type Props = {
  pokemonId: number
  alt: string
  size?: number
  className?: string
}

export function PokemonImage({ pokemonId, alt, size = 72, className }: Props) {
  const sources = useMemo(() => [pokemonArtworkUrl(pokemonId), pokemonSpriteUrl(pokemonId)], [pokemonId])

  const [state, setState] = useState<{ pokemonId: number; index: number; broken: boolean }>(() => ({
    pokemonId,
    index: 0,
    broken: false,
  }))

  const index = state.pokemonId === pokemonId ? state.index : 0
  const broken = state.pokemonId === pokemonId ? state.broken : false

  return (
    <div
      className={cn('grid place-items-center overflow-hidden rounded-md border bg-muted', className)}
      style={{ width: size, height: size }}
    >
      {broken ? (
        <div className="text-xs text-muted-foreground">#{pokemonId}</div>
      ) : (
        <img
          src={sources[index]}
          alt={alt}
          width={size}
          height={size}
          loading="lazy"
          className="h-full w-full object-contain"
          onError={() => {
            setState((prev) => {
              const current = prev.pokemonId === pokemonId ? prev : { pokemonId, index: 0, broken: false }
              if (current.index + 1 < sources.length) return { ...current, index: current.index + 1 }
              return { ...current, broken: true }
            })
          }}
        />
      )}
    </div>
  )
}
