package main

import (
	"fmt"
	"peso/internal/config"
	"peso/internal/math"
)

func foo(a bool) bool {
	return a
}

func main() {
	cfg := config.LoadConfig()
	fmt.Println(cfg.Start)

	r, _ := math.Calc("1+1")
	fmt.Println(r)
}
