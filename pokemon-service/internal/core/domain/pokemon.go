package domain

type Pokemon struct {
	ID     int
	Name   string
	Sprite string
	Types  []string
	Stats  map[string]int
}
