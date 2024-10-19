package math

import "testing"

func TestSum(t *testing.T) {
	tests := []struct {
		name       string
		expression string
		wantRes    float64
		wantErr    error
	}{
		{
			name:       "2+2",
			expression: "2+2",
			wantRes:    4,
			wantErr:    nil,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			gotRes, gotErr := Calc(tc.expression)
			if gotRes != tc.wantRes && gotErr != tc.wantErr {
				t.Fatal()
			}
		})
	}
}
