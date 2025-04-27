package domain

import (
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Token struct {
	ID      string    `gorm:"type:uuid;primaryKey" json:"id"`
	Sub     string    `gorm:"not null" json:"sub"`
	Exp     time.Time `gorm:"not null" json:"exp"`
	Revoked bool      `gorm:"default:false" json:"revoked"`
}

type TokenClaims struct {
	jwt.RegisteredClaims
}
