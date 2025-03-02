package domain

import (
	"github.com/lib/pq"
)

type Pokemon struct {
	ID    int            `json:"id" gorm:"primaryKey"`
	Name  string         `json:"name" gorm:"column:name;type:varchar(255);not null"`
	Types pq.StringArray `json:"types" gorm:"column:types;type:text[];not null"`
}
