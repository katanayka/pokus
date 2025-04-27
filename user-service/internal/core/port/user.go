package port

import (
	"context"

	"github.com/katanayka/pokus/user-service/internal/core/domain"
)

type UserRepository interface {
	CreateUser(ctx context.Context, user *domain.User) error
	GetUserByID(ctx context.Context, id uint) (*domain.User, error)
	GetUserByUsername(ctx context.Context, username string) (*domain.User, error)
	ListUsers(ctx context.Context, skip, limit uint) ([]domain.User, error)
	UpdateUser(ctx context.Context, user *domain.User) error
	DeleteUser(ctx context.Context, id uint) error
}

type UserService interface {
	Register(ctx context.Context, user *domain.User) error
	GetUser(ctx context.Context, id uint) (*domain.User, error)
	ListUsers(ctx context.Context, skip, limit uint64) ([]domain.User, error)
	UpdateUser(ctx context.Context, user *domain.User) error
	DeleteUser(ctx context.Context, id uint) error
}
