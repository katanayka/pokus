package http

import (
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/katanayka/pokus/pokemon-service/internal/adapter/config"
)

type Router struct {
	*gin.Engine
}

func NewRouter(
	config *config.HTTP,
	pokemonHandler PokemonHandler,
) (*Router, error) {
	if config.Env == "prod" {
		gin.SetMode(gin.ReleaseMode)
	}
	// f, _ := os.Create("gin.log")
	// gin.DefaultWriter = io.MultiWriter(f)
	router := gin.Default()

	router.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"}, // Разрешает запросы со всех источников
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Content-Type", "Authorization"},
		AllowCredentials: true,
	}))

	v1 := router.Group("/v1")
	{
		pokemon := v1.Group("/pokemons")
		{
			pokemon.GET("/name/:name", pokemonHandler.GetPokemonByName)
			pokemon.GET("/id/:id", pokemonHandler.GetPokemonByID)
			pokemon.GET("/:page", pokemonHandler.GetPokemonList)
			pokemon.GET("/", pokemonHandler.GetPokemonList)
		}
	}
	return &Router{
		router,
	}, nil
}
