package main

import (
	"testing"
)

func TestMultiply(t *testing.T) {
	tests := []struct {
		name string
		got  bool
		want bool
	}{
		{
			name: "true",
			got:  true,
			want: true,
		},
		{
			name: "false",
			got:  false,
			want: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := foo(tc.got)
			if got != tc.want {
				t.Fatal()
			}
		})
	}
}
