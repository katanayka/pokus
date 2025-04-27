package redis

import (
	"context"
	"time"

	"github.com/katanayka/pokus/pokemon-service/internal/adapter/config"
	"github.com/katanayka/pokus/pokemon-service/internal/core/port"
	"github.com/redis/go-redis/v9"
)

type Redis struct {
	client *redis.Client
}

func (r *Redis) Get(ctx context.Context, key string) ([]byte, error) {
	res, err := r.client.Get(ctx, key).Result()
	bytes := []byte(res)
	return bytes, err
}

func (r *Redis) Set(ctx context.Context, key string, value []byte, ttl time.Duration) error {
	return r.client.Set(ctx, key, value, ttl).Err()
}

func (r *Redis) Close() error {
	return r.client.Close()
}

func New(ctx context.Context, config *config.Redis) (port.CacheRepository, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     config.Addr,
		Password: config.Password,
		DB:       0,
	})
	_, err := client.Ping(ctx).Result()
	if err != nil {
		return nil, err
	}
	return &Redis{client}, nil
}
