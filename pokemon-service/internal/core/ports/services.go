// internal/core/ports/services.go
package ports

import (
	"context"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
)

type PokemonService interface {
	GetPokemon(ctx context.Context, id int) (*domain.Pokemon, error)
	CreatePokemon(ctx context.Context, pokemon domain.Pokemon) (int, error)
}
