package port

import (
	"context"

	"github.com/katanayka/pokus/auth-service/internal/core/domain"
)

type TokenPair struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
}

type TokenService interface {
	CreateTokenPair(ctx context.Context, sub string) (*TokenPair, error)
	RefreshTokenPair(ctx context.Context, refreshToken string) (*TokenPair, error)
	VerifyToken(ctx context.Context, accessToken string) (*domain.TokenClaims, error)
	RevokeRefreshToken(ctx context.Context, refreshToken string) error
}

type TokenRepository interface {
	CreateRefreshToken(ctx context.Context, token *domain.Token) error
	FindRefreshToken(ctx context.Context, id string) (*domain.Token, error)
	RevokeRefreshToken(ctx context.Context, refreshToken string) error
	DeleteExpiredTokens(ctx context.Context) error
}
