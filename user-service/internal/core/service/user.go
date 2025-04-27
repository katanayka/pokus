package service

import (
	"context"

	"github.com/katanayka/pokus/user-service/internal/core/domain"
	"github.com/katanayka/pokus/user-service/internal/core/port"
)

type UserService struct {
	repo port.UserRepository
}

// TODO: add validation and caching for user data

// DeleteUser implements port.UserService.
func (u *UserService) DeleteUser(ctx context.Context, id uint) error {
	return u.repo.DeleteUser(ctx, id)
}

// GetUser implements port.UserService.
func (u *UserService) GetUser(ctx context.Context, id uint) (*domain.User, error) {
	return u.repo.GetUserByID(ctx, id)
}

// ListUsers implements port.UserService.
func (u *UserService) ListUsers(ctx context.Context, skip uint64, limit uint64) ([]domain.User, error) {
	return u.repo.ListUsers(ctx, uint(skip), uint(limit))
}

// Register implements port.UserService.
func (u *UserService) Register(ctx context.Context, user *domain.User) error {
	return u.repo.CreateUser(ctx, user)
}

// UpdateUser implements port.UserService.
func (u *UserService) UpdateUser(ctx context.Context, user *domain.User) error {
	return u.repo.UpdateUser(ctx, user)
}

func NewUserService(repo port.UserRepository) port.UserService {
	return &UserService{
		repo,
	}
}
