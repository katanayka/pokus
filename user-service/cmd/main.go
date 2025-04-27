package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"strconv"
	"syscall"

	"github.com/katanayka/pokus/user-service/internal/adapter/storage/postgres/repository"
	"github.com/katanayka/pokus/user-service/internal/core/domain"
	"github.com/katanayka/pokus/user-service/internal/core/service"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	dbURL := "postgres://postgres:9191@localhost:5432/user_db?sslmode=disable"
	db, err := gorm.Open(postgres.Open(dbURL), &gorm.Config{})
	if err != nil {
		log.Fatalf("Unable to connect to database: %v", err)
	}

	if err := db.AutoMigrate(&domain.User{}); err != nil {
		log.Fatalf("Failed to auto-migrate schema: %v", err)
	}
	ctx := context.Background()

	userRepo := repository.NewUserRepository(db)
	userService := service.NewUserService(userRepo)

	for i := 0; i < 10; i++ {
		userService.Register(ctx, &domain.User{
			Username: strconv.Itoa(i),
			Email:    strconv.Itoa(i),
			Password: "123",
		})
	}

	userService.DeleteUser(ctx, 28)

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down server...")

	log.Println("Server exiting")
}
