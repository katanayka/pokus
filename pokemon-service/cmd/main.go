package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"

	"github.com/katanayka/pokus/pokemon-service/internal/adapters/handlers"
	"github.com/katanayka/pokus/pokemon-service/internal/adapters/pg"
	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
	"github.com/katanayka/pokus/pokemon-service/internal/core/services"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found")
	}

	// Connect to database using GORM
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://postgres:9191@localhost:5432/pokemon_db?sslmode=disable"
	}

	db, err := gorm.Open(postgres.Open(dbURL), &gorm.Config{})
	if err != nil {
		log.Fatalf("Unable to connect to database: %v", err)
	}

	// Auto-migrate the schema
	if err := db.AutoMigrate(&domain.Pokemon{}); err != nil {
		log.Fatalf("Failed to auto-migrate schema: %v", err)
	}

	pokemonRepo := pg.NewPokemonRepository(db)

	// Setup services
	pokemonService := services.NewPokemonService(pokemonRepo)

	// Setup HTTP handlers
	router := gin.Default()
	handlers.NewPokemonHandler(router, pokemonService)

	// Start server
	srv := &http.Server{
		Addr:    ":8080",
		Handler: router,
	}

	// Graceful shutdown
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %s\n", err)
		}
	}()

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
