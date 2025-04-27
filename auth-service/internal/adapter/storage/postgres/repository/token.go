package repository

import (
	"context"
	"time"

	"github.com/katanayka/pokus/auth-service/internal/core/domain"
	"github.com/katanayka/pokus/auth-service/internal/core/port"
	"gorm.io/gorm"
)

type tokenRepository struct {
	db *gorm.DB
}

// CreateRefreshToken implements port.TokenRepository.
func (r *tokenRepository) CreateRefreshToken(ctx context.Context, token *domain.Token) error {
	return r.db.WithContext(ctx).Create(token).Error
}

// DeleteExpiredTokens implements port.TokenRepository.
func (r *tokenRepository) DeleteExpiredTokens(ctx context.Context) error {
	return r.db.WithContext(ctx).Where("exp < ?", time.Now()).Delete(&domain.Token{}).Error
}

// FindRefreshToken implements port.TokenRepository.
func (r *tokenRepository) FindRefreshToken(ctx context.Context, id string) (*domain.Token, error) {
	var t domain.Token
	err := r.db.WithContext(ctx).Where("id = ?", id).First(&t).Error
	if err == gorm.ErrRecordNotFound {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &t, nil
}

// RevokeRefreshToken implements port.TokenRepository.
func (r *tokenRepository) RevokeRefreshToken(ctx context.Context, refreshToken string) error {
	return r.db.WithContext(ctx).Model(&domain.Token{}).Where("id = ?", refreshToken).Update("revoked", true).Error
}

func NewTokenRepository(db *gorm.DB) port.TokenRepository {
	return &tokenRepository{
		db: db,
	}
}
