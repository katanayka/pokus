package math

import (
	"errors"
	"testing"
)

func TestCalc(t *testing.T) {
	tests := []struct {
		name       string
		expression string
		wantRes    float64
		wantErr    error
	}{
		{
			name:       "Сложение",
			expression: "2 + 2",
			wantRes:    4,
			wantErr:    nil,
		},
		{
			name:       "Вычитание",
			expression: "5 - 3",
			wantRes:    2,
			wantErr:    nil,
		},
		{
			name:       "Умножение",
			expression: "3 * 4",
			wantRes:    12,
			wantErr:    nil,
		},
		{
			name:       "Деление",
			expression: "8 / 2",
			wantRes:    4,
			wantErr:    nil,
		},
		// Сложные операции
		{
			name:       "Сложение и вычитание",
			expression: "1 + 2 - 3",
			wantRes:    0,
			wantErr:    nil,
		},
		{
			name:       "Сложение, вычитание, умножение",
			expression: "1 + 2 * 3 - 4",
			wantRes:    3,
			wantErr:    nil,
		},
		{
			name:       "Сложение, умножение и деление",
			expression: "6 / 2 * 3 + 1",
			wantRes:    10,
			wantErr:    nil,
		},
		{
			name:       "Сложение, вычитание, деление",
			expression: "10 - 5 + 2",
			wantRes:    7,
			wantErr:    nil,
		},
		// Использование скобок
		{
			name:       "Скобки",
			expression: "(1 + 2) * 3",
			wantRes:    9,
			wantErr:    nil,
		},
		{
			name:       "Скобки и приоритет",
			expression: "2 * (3 + 4) - 1",
			wantRes:    13,
			wantErr:    nil,
		},
		{
			name:       "Вложенные скобки",
			expression: "(1 + (2 - 3) * 4) / 2",
			wantRes:    -1.5,
			wantErr:    nil,
		},
		// Сложные операции с float64
		{
			name:       "Сложение и вычитание с дробными",
			expression: "1.5 + 2.2 - 0.7",
			wantRes:    3.0,
			wantErr:    nil,
		},
		{
			name:       "Сложение, вычитание, умножение с дробными",
			expression: "1.2 + 2.3 * 3.5 - 4.1",
			wantRes:    5.15,
			wantErr:    nil,
		},
		{
			name:       "Сложение, умножение и деление с дробными",
			expression: "6.0 / 2.0 * 3.5 + 1.5",
			wantRes:    12,
			wantErr:    nil,
		},
		{
			name:       "Сложение, вычитание, деление с дробными",
			expression: "10.0 - 5.0 + 2.5",
			wantRes:    7.5,
			wantErr:    nil,
		},
		// Использование скобок
		{
			name:       "Скобки с дробными",
			expression: "(1.5 + 2.5) * 3.0",
			wantRes:    12.0,
			wantErr:    nil,
		},
		{
			name:       "Скобки и приоритет с дробными",
			expression: "2.0 * (3.5 + 4.5) - 1.0",
			wantRes:    15.0,
			wantErr:    nil,
		},
		{
			name:       "Вложенные скобки с дробными",
			expression: "(1.0 + (2.5 - 3.5) * 4.0) / 2.0",
			wantRes:    -1.5,
			wantErr:    nil,
		},
		// Ошибки
		{
			name:       "Деление на ноль",
			expression: "5 / 0",
			wantRes:    0,
			wantErr:    errors.New("division by zero"),
		},
		{
			name:       "Некорректное выражение",
			expression: "2 + + 3",
			wantRes:    0,
			wantErr:    errors.New("invalid expression"),
		},
		{
			name:       "нет открывающей скобки",
			expression: "5 * (3 + 2))",
			wantRes:    0,
			wantErr:    errors.New("invalid expression"),
		},
		{
			name:       "Нет закрывающей скобки",
			expression: "1 + (2 - 3",
			wantRes:    0,
			wantErr:    errors.New("invalid expression"),
		},
		{
			name:       "Пустое выражение",
			expression: "",
			wantRes:    0,
			wantErr:    errors.New("invalid expression"),
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			gotRes, gotErr := Calc(tc.expression)
			if gotRes != tc.wantRes || (gotErr != nil && gotErr.Error() != tc.wantErr.Error()) {
				t.Fatalf("полученный результат: %v\nполученная ошибка: %v\nожидаемый результат: %v\nожидаемая ошибка: %v\n", gotRes, gotErr, tc.wantRes, tc.wantErr)
			}
		})
	}
}
