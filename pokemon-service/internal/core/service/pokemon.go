package service

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
	"github.com/katanayka/pokus/pokemon-service/internal/core/port"
)

type PokemonService struct {
	repo  port.PokemonRepository
	cache port.CacheRepository
}

func (pok *PokemonService) GetPokemonList(ctx context.Context, perPage, page int) ([]*domain.Pokemon, error) {
	cacheKey := fmt.Sprintf("pokemon:list:page:%d", page)
	cachedPokemonList, err := pok.cache.Get(ctx, cacheKey)
	if err == nil {
		var pokemonList []*domain.Pokemon
		err := json.Unmarshal([]byte(cachedPokemonList), &pokemonList)
		if err != nil {
			return nil, domain.ErrInternal
		}
		return pokemonList, nil
	}

	pokemonList, err := pok.repo.GetList(ctx, perPage, page)
	if err != nil {
		return nil, err
	}

	pokemonListData, err := json.Marshal(pokemonList)
	if err != nil {
		return nil, domain.ErrInternal
	}

	err = pok.cache.Set(ctx, cacheKey, pokemonListData, time.Hour)
	if err != nil {
		return nil, domain.ErrInternal
	}
	return pokemonList, nil
}

func (pok *PokemonService) GetPokemonByID(ctx context.Context, id int) (*domain.Pokemon, error) {
	cackeKey := fmt.Sprintf("pokemon:id:%d", id)
	cachedPokemon, err := pok.cache.Get(ctx, cackeKey)
	if err == nil {
		var pokemon *domain.Pokemon
		err := json.Unmarshal([]byte(cachedPokemon), &pokemon)
		if err != nil {
			return nil, domain.ErrInternal
		}
		return pokemon, nil
	}
	pokemon, err := pok.repo.GetByID(ctx, id)
	if err != nil {
		return nil, err
	}

	pokemonData, err := json.Marshal(pokemon)
	if err != nil {
		return nil, domain.ErrInternal
	}

	err = pok.cache.Set(ctx, cackeKey, pokemonData, time.Hour)
	if err != nil {
		return nil, domain.ErrInternal
	}
	return pokemon, nil
}

func (pok *PokemonService) GetPokemonByName(ctx context.Context, name string) (*domain.Pokemon, error) {
	cackeKey := fmt.Sprintf("pokemon:name:%s", name)
	cachedPokemon, err := pok.cache.Get(ctx, cackeKey)
	if err == nil {
		var pokemon *domain.Pokemon
		err := json.Unmarshal([]byte(cachedPokemon), &pokemon)
		if err != nil {
			return nil, domain.ErrInternal
		}
		return pokemon, nil
	}
	pokemon, err := pok.repo.GetByName(ctx, name)
	if err != nil {
		return nil, err
	}

	pokemonData, err := json.Marshal(pokemon)
	if err != nil {
		return nil, domain.ErrInternal
	}

	err = pok.cache.Set(ctx, cackeKey, pokemonData, time.Hour)
	if err != nil {
		return nil, domain.ErrInternal
	}
	return pok.repo.GetByName(ctx, name)
}

func (pok *PokemonService) SayHello(ctx context.Context) (string, error) {
	return "Hello from Pokus", nil
}

func NewPokemonService(repo port.PokemonRepository, cache port.CacheRepository) port.PokemonService {
	return &PokemonService{
		repo,
		cache,
	}
}
