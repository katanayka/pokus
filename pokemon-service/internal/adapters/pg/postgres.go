// internal/adapters/pg/postgres.go
package pg

import (
	"context"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
	"github.com/katanayka/pokus/pokemon-service/internal/core/ports"
	"gorm.io/gorm"
)

type pokemonRepository struct {
	db *gorm.DB
}

func NewPokemonRepository(db *gorm.DB) ports.PokemonRepository {
	return &pokemonRepository{
		db: db,
	}
}

func (r *pokemonRepository) GetByID(ctx context.Context, id int) (*domain.Pokemon, error) {
	var pokemon domain.Pokemon
	if err := r.db.WithContext(ctx).First(&pokemon, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, nil
		}
		return nil, err
	}
	return &pokemon, nil
}

func (r *pokemonRepository) GetAll(ctx context.Context) ([]domain.Pokemon, error) {
	var pokemons []domain.Pokemon
	if err := r.db.WithContext(ctx).Find(&pokemons).Error; err != nil {
		return nil, err
	}
	return pokemons, nil
}

func (r *pokemonRepository) Create(ctx context.Context, pokemon domain.Pokemon) (int, error) {
	if err := r.db.WithContext(ctx).Create(&pokemon).Error; err != nil {
		return 0, err
	}
	return pokemon.ID, nil
}
