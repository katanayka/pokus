package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
	"github.com/katanayka/pokus/pokemon-service/internal/core/ports"
)

type PokemonHandler struct {
	service ports.PokemonService
}

func NewPokemonHandler(r *gin.Engine, service ports.PokemonService) {
	handler := &PokemonHandler{
		service: service,
	}

	g := r.Group("/api/v1/pokemon")
	{
		g.GET("/:id", handler.Get)
		g.POST("", handler.Create)
		g.GET("", handler.GetAll)
	}
}

func (h *PokemonHandler) Get(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID format"})
		return
	}

	pokemon, err := h.service.GetPokemon(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if pokemon == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Pokemon not found"})
		return
	}

	c.JSON(http.StatusOK, pokemon)
}

func (h *PokemonHandler) GetAll(c *gin.Context) {
	pokemons, err := h.service.GetAllPokemons(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, pokemons)
}

func (h *PokemonHandler) Create(c *gin.Context) {
	var pokemon domain.Pokemon
	if err := c.ShouldBindJSON(&pokemon); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	id, err := h.service.CreatePokemon(c.Request.Context(), pokemon)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"id": id})
}
