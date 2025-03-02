// internal/core/services/pokemon_service.go
package services

import (
	"context"
	"errors"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
	"github.com/katanayka/pokus/pokemon-service/internal/core/ports"
)

type pokemonService struct {
	repo ports.PokemonRepository
}

func NewPokemonService(repo ports.PokemonRepository) ports.PokemonService {
	return &pokemonService{
		repo: repo,
	}
}

func (s *pokemonService) GetPokemon(ctx context.Context, id int) (*domain.Pokemon, error) {
	if id <= 0 {
		return nil, errors.New("invalid pokemon ID")
	}
	return s.repo.GetByID(ctx, id)
}

func (s *pokemonService) CreatePokemon(ctx context.Context, pokemon domain.Pokemon) (int, error) {
	if pokemon.Name == "" {
		return 0, errors.New("pokemon name is required")
	}
	return s.repo.Create(ctx, pokemon)
}
