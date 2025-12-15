package main

import (
	"log"
	"os"
)

func main() {
	if os.Getenv("NOTIFY_TOKEN") == "" {
		log.Fatal("NOTIFY_TOKEN env var is required")
	}
	router := SetupRouter()
	log.Println("Notification service listening on :8081")
	if err := router.Run(":8081"); err != nil {
		log.Fatal(err)
	}
}
