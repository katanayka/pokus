package port

import "context"

type AuthService interface {
	Login(ctx context.Context, email, password string) error
	Logout(ctx context.Context, accessToken string) error
}
