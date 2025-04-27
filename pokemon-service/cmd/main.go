package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/katanayka/pokus/pokemon-service/internal/adapter/config"
	h "github.com/katanayka/pokus/pokemon-service/internal/adapter/handler/http"
	r "github.com/katanayka/pokus/pokemon-service/internal/adapter/storage/pokeapi"
	"github.com/katanayka/pokus/pokemon-service/internal/adapter/storage/redis"
	s "github.com/katanayka/pokus/pokemon-service/internal/core/service"
)

func main() {
	// load environment variables
	config, err := config.New()
	if err != nil {
		log.Print("Error loading environment variables ", err)
		os.Exit(1)
	}
	ctx := context.Background()

	// init cache
	cache, err := redis.New(ctx, config.Redis)
	if err != nil {
		log.Println("Error initializing cache ", err)
		os.Exit(1)
	}
	defer cache.Close()

	// init dependencies
	pokemonRepo := r.NewPokemonRepository("https://pokeapi.co/api/v2/")
	pokemonService := s.NewPokemonService(pokemonRepo, cache)
	pokemonHandler := h.NewPokemonHandler(pokemonService)

	// init server
	router, _ := h.NewRouter(
		config.HTTP,
		*pokemonHandler,
	)

	srv := &http.Server{
		Addr:    fmt.Sprintf("%s:%s", config.HTTP.URL, config.HTTP.Port),
		Handler: router,
	}

	// start server
	log.Printf("Server running on: %s", srv.Addr)
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %s\n", err)
		}
	}()

	// graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}

	log.Println("Server exiting")
}
