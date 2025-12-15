package main

type Message struct {
	UserID  string
	Payload []byte
}

type Hub struct {
	register   chan *Client
	unregister chan *Client
	broadcast  chan Message
	clients    map[string]*Client
}

func NewHub() *Hub {
	return &Hub{
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan Message),
		clients:    map[string]*Client{},
	}
}

func (h *Hub) Run() {
	for {
		select {
		case c := <-h.register:
			h.clients[c.userID] = c
		case c := <-h.unregister:
			delete(h.clients, c.userID)
			close(c.send)
		case msg := <-h.broadcast:
			if client, ok := h.clients[msg.UserID]; ok {
				client.send <- msg.Payload
			}
		}
	}
}
