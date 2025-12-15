package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"os"
	"strings"
)

type NotifyRequest struct {
	UserID  int                    `json:"user_id"`
	Event   string                 `json:"event"`
	Payload map[string]interface{} `json:"payload"`
}

func HttpNotify(hub *Hub, c *gin.Context) {
	expectedToken := os.Getenv("NOTIFY_TOKEN")
	if expectedToken == "" {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "NOTIFY_TOKEN is not configured"})
		return
	}
	auth := c.GetHeader("Authorization")
	if !strings.HasPrefix(auth, "Bearer ") {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}
	token := strings.TrimPrefix(auth, "Bearer ")
	if subtle.ConstantTimeCompare([]byte(token), []byte(expectedToken)) != 1 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	var req NotifyRequest
	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	switch req.Event {
	case "battle_started", "battle_ended", "victory", "defeat":
	default:
		c.JSON(http.StatusBadRequest, gin.H{"error": "unsupported event"})
		return
	}
	body, _ := json.Marshal(gin.H{"event": req.Event, "payload": req.Payload})
	hub.broadcast <- Message{UserID: fmt.Sprint(req.UserID), Payload: body}
	c.JSON(http.StatusOK, gin.H{"status": "sent"})
}
