package main

import (
	"context"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"errors"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/katanayka/pokus/auth-service/internal/adapter/storage/postgres/repository"
	"github.com/katanayka/pokus/auth-service/internal/core/domain"
	"github.com/katanayka/pokus/auth-service/internal/core/service"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// Config holds the application configuration
type Config struct {
	PrivateKeyPath             string
	PublicKeyPath              string
	DatabaseURL                string
	AccessTokenDurationMinutes int
	RefreshTokenDurationHours  int
}

// loadConfig loads configuration values (e.g., from env vars or a config file)
func loadConfig() Config {
	// Replace with your configuration loading logic
	return Config{
		PrivateKeyPath:             "keys/private.pem",
		PublicKeyPath:              "keys/public.pem",
		DatabaseURL:                "postgres://postgres:9191@localhost:5432/token_db?sslmode=disable",
		AccessTokenDurationMinutes: 2,
		RefreshTokenDurationHours:  2,
	}
}

// loadPrivateKey loads an RSA private key from a PEM file
func loadPrivateKey(path string) (*rsa.PrivateKey, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	block, _ := pem.Decode(data)
	if block == nil {
		return nil, errors.New("failed to decode PEM block")
	}
	key, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	if err != nil {
		return nil, err
	}

	privateKey, ok := key.(*rsa.PrivateKey)
	if !ok {
		return nil, errors.New("not an RSA private key")
	}
	return privateKey, nil
}

// loadPublicKey loads an RSA public key from a PEM file
func loadPublicKey(path string) (*rsa.PublicKey, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	block, _ := pem.Decode(data)
	if block == nil {
		return nil, errors.New("failed to decode PEM block")
	}
	pub, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		return nil, err
	}
	publicKey, ok := pub.(*rsa.PublicKey)
	if !ok {
		return nil, errors.New("not an RSA public key")
	}
	return publicKey, nil
}

func main() {
	config := loadConfig()

	privateKey, err := loadPrivateKey(config.PrivateKeyPath)
	if err != nil {
		log.Fatalf("Failed to load private key: %v", err)
	}
	publicKey, err := loadPublicKey(config.PublicKeyPath)
	if err != nil {
		log.Fatalf("Failed to load public key: %v", err)
	}

	db, err := gorm.Open(postgres.Open(config.DatabaseURL), &gorm.Config{})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	err = db.AutoMigrate(&domain.Token{})
	if err != nil {
		log.Fatalf("Failed to migrate database: %v", err)
	}

	tokenRepo := repository.NewTokenRepository(db) // Adjust to your implementation

	accessDuration := time.Duration(config.AccessTokenDurationMinutes) * time.Second
	refreshDuration := time.Duration(config.RefreshTokenDurationHours) * time.Second

	tokenService := service.NewTokenService(tokenRepo, privateKey, publicKey, accessDuration, refreshDuration)

	log.Println("Token service initialized successfully")

	ctx := context.Background()
	userId := fmt.Sprintf("%d", uint(1))

	tokenPair, err := tokenService.CreateTokenPair(ctx, userId)
	if err != nil {
		log.Fatalf("Failed to create token pair: %v", err)
	}

	log.Println("Token pair created successfully")
	log.Printf("Access Token: %s\n", tokenPair.AccessToken)
	log.Printf("Refresh Token: %s\n", tokenPair.RefreshToken)

	claims, err := tokenService.VerifyToken(ctx, tokenPair.AccessToken)
	if err != nil {
		log.Fatalf("Failed to verify token: %v", err)
	}

	log.Println("Token verified successfully")
	log.Printf("Claims: %+v\n", claims)

	newTokenPair, err := tokenService.RefreshTokenPair(ctx, tokenPair.RefreshToken)
	if err != nil {
		log.Fatalf("Failed to refresh token: %v", err)
	}

	log.Println("Token pair refreshed successfully")
	log.Printf("New Access Token: %s\n", newTokenPair.AccessToken)
	log.Printf("New Refresh Token: %s\n", newTokenPair.RefreshToken)

	// tokenRepo.DeleteExpiredTokens(ctx)

	err = tokenService.RevokeRefreshToken(ctx, newTokenPair.RefreshToken)
	if err != nil {
		log.Fatalf("Failed to revoke refresh token: %v", err)
	}

	log.Println("Refresh token revoked successfully")

	log.Println("Token service testing completed")
}
