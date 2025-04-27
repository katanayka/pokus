package repository

import (
	"context"

	"github.com/katanayka/pokus/user-service/internal/core/domain"
	"github.com/katanayka/pokus/user-service/internal/core/port"
	"gorm.io/gorm"
)

type UserRepository struct {
	db *gorm.DB
}

// CreateUser implements port.UserRepository.
func (u *UserRepository) CreateUser(ctx context.Context, user *domain.User) error {
	return u.db.WithContext(ctx).Create(user).Error
}

// DeleteUser implements port.UserRepository.
func (u *UserRepository) DeleteUser(ctx context.Context, id uint) error {
	if err := u.db.WithContext(ctx).Delete(&domain.User{}, id).Error; err != nil {
		return err
	}
	return nil
}

// GetUserByID implements port.UserRepository.
func (u *UserRepository) GetUserByID(ctx context.Context, id uint) (*domain.User, error) {
	panic("unimplemented")
}

// GetUserByUsername implements port.UserRepository.
func (u *UserRepository) GetUserByUsername(ctx context.Context, username string) (*domain.User, error) {
	panic("unimplemented")
}

// ListUsers implements port.UserRepository.
func (u *UserRepository) ListUsers(ctx context.Context, skip uint, limit uint) ([]domain.User, error) {
	panic("unimplemented")
}

// UpdateUser implements port.UserRepository.
func (u *UserRepository) UpdateUser(ctx context.Context, user *domain.User) error {
	panic("unimplemented")
}

func NewUserRepository(db *gorm.DB) port.UserRepository {
	return &UserRepository{
		db: db,
	}
}
