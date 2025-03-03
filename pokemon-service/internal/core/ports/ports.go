package ports

import (
	"context"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
)

type PokemonRepository interface {
	GetByID(ctx context.Context, id int) (*domain.Pokemon, error)
	GetAll(ctx context.Context) ([]domain.Pokemon, error)
	Create(ctx context.Context, pokemon domain.Pokemon) (int, error)
}

type PokemonService interface {
	GetPokemon(ctx context.Context, id int) (*domain.Pokemon, error)
	GetAllPokemons(ctx context.Context) ([]domain.Pokemon, error)
	CreatePokemon(ctx context.Context, pokemon domain.Pokemon) (int, error)
}
