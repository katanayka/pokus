package main

import (
	"testing"
	"time"
)

func TestHub_UnregisterRemovesClientAndClosesChannel(t *testing.T) {
	hub := NewHub()
	go hub.Run()

	c := &Client{hub: hub, conn: nil, send: make(chan []byte, 1), userID: "42"}
	hub.register <- c

	hub.unregister <- c

	select {
	case _, ok := <-c.send:
		if ok {
			t.Fatal("expected send channel to be closed")
		}
	case <-time.After(1 * time.Second):
		t.Fatal("timed out waiting for channel close")
	}
}
