package repository

import (
	"context"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
	"github.com/katanayka/pokus/pokemon-service/internal/core/port"
	"gorm.io/gorm"
)

type PokemonRepository struct {
	db *gorm.DB
}

func (p *PokemonRepository) GetList(ctx context.Context, perPage, page int) ([]*domain.Pokemon, error) {
	panic("unimplemented")
}

func (p *PokemonRepository) GetByID(ctx context.Context, id int) (*domain.Pokemon, error) {
	panic("unimplemented")
}

func (p *PokemonRepository) GetByName(ctx context.Context, name string) (*domain.Pokemon, error) {
	panic("unimplemented")
}

func NewPokemonRepository(db *gorm.DB) port.PokemonRepository {
	return &PokemonRepository{
		db,
	}
}
