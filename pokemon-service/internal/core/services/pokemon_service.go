package services

import (
	"context"

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
	return s.repo.GetByID(ctx, id)
}

func (s *pokemonService) GetAllPokemons(ctx context.Context) ([]domain.Pokemon, error) {
	return s.repo.GetAll(ctx)
}

func (s *pokemonService) CreatePokemon(ctx context.Context, pokemon domain.Pokemon) (int, error) {
	return s.repo.Create(ctx, pokemon)
}
