package http

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/katanayka/pokus/pokemon-service/internal/core/port"
)

type PokemonHandler struct {
	svc port.PokemonService
}

func NewPokemonHandler(svc port.PokemonService) *PokemonHandler {
	return &PokemonHandler{
		svc,
	}
}

type GetPokemonByNameRequest struct {
	Name string `uri:"name" binding:"required"`
}

func (ph *PokemonHandler) GetPokemonByName(ctx *gin.Context) {
	var req GetPokemonByNameRequest
	if err := ctx.ShouldBindUri(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request parameters",
			"details": err.Error(),
		})
		return
	}

	pokemon, err := ph.svc.GetPokemonByName(ctx, req.Name)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to retrieve pokemon",
			"details": err.Error(),
		})
		return
	}

	ctx.JSON(http.StatusOK, pokemon)
}

type GetPokemonByIDRequest struct {
	ID int `uri:"id" binding:"required"`
}

func (ph *PokemonHandler) GetPokemonByID(ctx *gin.Context) {
	var req GetPokemonByIDRequest
	if err := ctx.ShouldBindUri(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request parameters",
			"details": err.Error(),
		})
		return
	}

	pokemon, err := ph.svc.GetPokemonByID(ctx, req.ID)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to retrieve pokemon",
			"details": err.Error(),
		})
		return
	}

	ctx.JSON(http.StatusOK, pokemon)
}

type GetPokemonListRequest struct {
	Page int `uri:"page"`
}

func (ph *PokemonHandler) GetPokemonList(ctx *gin.Context) {
	var req GetPokemonListRequest
	if err := ctx.ShouldBindUri(&req); err != nil || req.Page <= 0 {
		req.Page = 1
	}

	perPage := 12

	pokemons, err := ph.svc.GetPokemonList(ctx, perPage, req.Page)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to retrieve pokemon",
			"details": err.Error(),
		})
		return
	}

	ctx.JSON(http.StatusOK, pokemons)
}
