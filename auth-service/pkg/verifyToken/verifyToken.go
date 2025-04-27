package verifytoken

import (
	"crypto/rsa"
	"errors"

	"github.com/golang-jwt/jwt/v5"
)

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
