package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type (
	Containter struct {
		HTTP  *HTTP
		Redis *Redis
	}
	HTTP struct {
		Env  string
		URL  string
		Port string
	}
	Redis struct {
		Addr     string
		Password string
	}
)

func New() (*Containter, error) {
	if err := godotenv.Load(); err != nil {
		log.Fatalf("Error loading .env file: %v", err)
	}

	http := &HTTP{
		Env:  os.Getenv("APP_ENV"),
		URL:  os.Getenv("HTTP_URL"),
		Port: os.Getenv("HTTP_PORT"),
	}

	redis := &Redis{
		Addr:     os.Getenv("REDIS_ADDR"),
		Password: os.Getenv("REDIS_PASSWORD"),
	}

	return &Containter{
		HTTP:  http,
		Redis: redis,
	}, nil
}
