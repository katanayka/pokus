package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
)

func TestHttpNotify_UnauthorizedWithoutAuthHeader(t *testing.T) {
	t.Setenv("NOTIFY_TOKEN", "secret")
	gin.SetMode(gin.TestMode)
	hub := NewHub()

	r := gin.New()
	r.POST("/notify", func(c *gin.Context) { HttpNotify(hub, c) })

	w := httptest.NewRecorder()
	req := httptest.NewRequest("POST", "/notify", bytes.NewBufferString(`{"user_id":1,"event":"battle_started","payload":{}}`))
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected %d, got %d", http.StatusUnauthorized, w.Code)
	}
}

func TestHttpNotify_RejectsUnsupportedEvent(t *testing.T) {
	t.Setenv("NOTIFY_TOKEN", "secret")
	gin.SetMode(gin.TestMode)
	hub := NewHub()

	r := gin.New()
	r.POST("/notify", func(c *gin.Context) { HttpNotify(hub, c) })

	w := httptest.NewRecorder()
	req := httptest.NewRequest("POST", "/notify", bytes.NewBufferString(`{"user_id":1,"event":"nope","payload":{}}`))
	req.Header.Set("Authorization", "Bearer secret")
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected %d, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestHttpNotify_BroadcastsToConnectedClient(t *testing.T) {
	t.Setenv("NOTIFY_TOKEN", "secret")
	gin.SetMode(gin.TestMode)

	hub := NewHub()
	go hub.Run()

	client := &Client{hub: hub, conn: nil, send: make(chan []byte, 1), userID: "1"}
	hub.register <- client

	r := gin.New()
	r.POST("/notify", func(c *gin.Context) { HttpNotify(hub, c) })

	w := httptest.NewRecorder()
	req := httptest.NewRequest("POST", "/notify", bytes.NewBufferString(`{"user_id":1,"event":"battle_started","payload":{"battle_id":123}}`))
	req.Header.Set("Authorization", "Bearer secret")
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d (%s)", http.StatusOK, w.Code, w.Body.String())
	}

	select {
	case msg := <-client.send:
		var body map[string]interface{}
		if err := json.Unmarshal(msg, &body); err != nil {
			t.Fatalf("invalid json message: %v", err)
		}
		if body["event"] != "battle_started" {
			t.Fatalf("expected event battle_started, got %v", body["event"])
		}
	case <-time.After(1 * time.Second):
		t.Fatal("timed out waiting for ws message")
	}
}
