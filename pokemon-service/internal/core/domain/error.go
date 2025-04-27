package domain

import (
	"errors"
)

var (
	ErrPokemonNotFound = errors.New("pokemon not found")
	ErrInternal        = errors.New("internal error")
)
