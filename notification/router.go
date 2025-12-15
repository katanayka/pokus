package main

import "github.com/gin-gonic/gin"

func SetupRouter() *gin.Engine {
	r := gin.Default()
	hub := NewHub()
	go hub.Run()
	r.GET("/ws", func(c *gin.Context) {
		ServeWs(hub, c)
	})
	r.POST("/notify", func(c *gin.Context) {
		HttpNotify(hub, c)
	})
	return r
}
