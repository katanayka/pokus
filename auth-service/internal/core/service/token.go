package service

import (
	"context"
	"crypto/rsa"
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/katanayka/pokus/auth-service/internal/core/domain"
	"github.com/katanayka/pokus/auth-service/internal/core/port"
)

type TokenService struct {
	repo            port.TokenRepository
	privateKey      *rsa.PrivateKey
	publicKey       *rsa.PublicKey
	accessLifetime  time.Duration
	refreshLifetime time.Duration
}

// CreateTokenPair implements port.TokenService.
func (t *TokenService) CreateTokenPair(ctx context.Context, sub string) (*port.TokenPair, error) {
	accessToken, err := t.generateAccessToken(sub)
	if err != nil {
		return nil, err
	}

	refreshToken, err := generateRefreshToken()
	if err != nil {
		return nil, err
	}

	expiresAt := time.Now().Add(t.refreshLifetime)
	tokenRecord := &domain.Token{
		ID:      refreshToken,
		Sub:     sub,
		Exp:     expiresAt,
		Revoked: false,
	}

	err = t.repo.CreateRefreshToken(ctx, tokenRecord)
	if err != nil {
		return nil, err
	}

	return &port.TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
	}, nil
}

// RefreshTokenPair implements port.TokenService.
func (t *TokenService) RefreshTokenPair(ctx context.Context, refreshToken string) (*port.TokenPair, error) {
	tokenRecord, err := t.repo.FindRefreshToken(ctx, refreshToken)
	if err != nil {
		return nil, err
	}
	if tokenRecord == nil {
		return nil, errors.New("refresh token not found")
	}
	if tokenRecord.Revoked {
		return nil, errors.New("refresh token has been revoked")
	}
	if time.Now().After(tokenRecord.Exp) {
		return nil, errors.New("refresh token has expired")
	}
	newAccesToken, err := t.generateAccessToken(tokenRecord.Sub)
	if err != nil {
		return nil, err
	}
	newRefreshToken, err := generateRefreshToken()
	if err != nil {
		return nil, err
	}
	newExpiresAt := time.Now().Add(t.refreshLifetime)
	newTokenRecord := &domain.Token{
		Sub:     tokenRecord.Sub,
		Exp:     newExpiresAt,
		Revoked: false,
	}
	err = t.repo.CreateRefreshToken(ctx, newTokenRecord)
	if err != nil {
		return nil, err
	}

	err = t.repo.RevokeRefreshToken(ctx, refreshToken)
	if err != nil {
		return nil, err
	}
	return &port.TokenPair{
		AccessToken:  newAccesToken,
		RefreshToken: newRefreshToken,
	}, nil
}

// RevokeRefreshToken implements port.TokenService.
func (t *TokenService) RevokeRefreshToken(ctx context.Context, refreshToken string) error {
	return t.repo.RevokeRefreshToken(ctx, refreshToken)
}

// VerifyToken implements port.TokenService.
func (t *TokenService) VerifyToken(ctx context.Context, accessToken string) (*domain.TokenClaims, error) {
	claims := &domain.TokenClaims{}
	token, err := jwt.ParseWithClaims(accessToken, claims, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
			return nil, errors.New("unexpected signing method")
		}
		return t.publicKey, nil
	})
	if err != nil {
		return nil, err
	}

	if token.Valid {
		return claims, nil
	}
	return nil, errors.New("invalid token")
}

func VerifyToken(publicKey *rsa.PublicKey, accessToken string) error {
	token, err := jwt.Parse(accessToken, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
			return nil, errors.New("unexpected signing method")
		}
		return publicKey, nil
	})
	if err != nil {
		return err
	}

	if token.Valid {
		return nil
	}
	return errors.New("invalid token")
}

//

func (t *TokenService) generateAccessToken(userId string) (string, error) {
	now := time.Now()
	claims := &domain.TokenClaims{
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userId,
			ExpiresAt: jwt.NewNumericDate(now.Add(t.accessLifetime)),
			IssuedAt:  jwt.NewNumericDate(now),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
	return token.SignedString(t.privateKey)
}

func generateRefreshToken() (string, error) {
	return uuid.NewString(), nil
}

func NewTokenService(
	tokenRepo port.TokenRepository,
	privateKey *rsa.PrivateKey,
	publicKey *rsa.PublicKey,
	accessLifetime time.Duration,
	refreshLifetime time.Duration,
) port.TokenService {
	return &TokenService{
		repo:            tokenRepo,
		privateKey:      privateKey,
		publicKey:       publicKey,
		accessLifetime:  accessLifetime,
		refreshLifetime: refreshLifetime,
	}
}
