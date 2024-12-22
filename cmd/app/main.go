package main

import (
	"log"
	"net/http"
	"peso/internal/api"
)

func main() {
	http.HandleFunc("/api/v1/calculate", api.CalculateHandler)

	log.Println("Server is running on http://localhost:8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
