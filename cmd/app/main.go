package main

import (
	"fmt"
)

func foo(a bool) bool {
	return a
}

func main() {
	fmt.Print(foo(true))
}
