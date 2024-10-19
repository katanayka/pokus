package config

import (
	"github.com/spf13/viper"
)

type Config struct {
	Start string
	Port  int
}

func LoadConfig() Config {
	viper.SetDefault("Start", "работаем.")

	config := Config{
		Start: viper.GetString("Start"),
	}

	return config
}
