// internal/core/ports/repositories.go
package ports

import (
	"context"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
)

type PokemonRepository interface {
	GetByID(ctx context.Context, id int) (*domain.Pokemon, error)
	Create(ctx context.Context, pokemon domain.Pokemon) (int, error)
}
