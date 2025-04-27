package port

import (
	"context"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
)

type PokemonRepository interface {
	GetByName(ctx context.Context, name string) (*domain.Pokemon, error)
	GetByID(ctx context.Context, id int) (*domain.Pokemon, error)
	GetList(ctx context.Context, perPage, page int) ([]*domain.Pokemon, error)
}

type PokemonService interface {
	GetPokemonByName(ctx context.Context, name string) (*domain.Pokemon, error)
	GetPokemonByID(ctx context.Context, id int) (*domain.Pokemon, error)
	GetPokemonList(ctx context.Context, perPage, page int) ([]*domain.Pokemon, error)
	SayHello(ctx context.Context) (string, error)
}
