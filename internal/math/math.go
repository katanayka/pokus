package math

import (
	"errors"
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

func deleteElement(s []string, index int) []string {
	return append(s[:index], s[index+1:]...)
}

func Operation(first string, operand string, second string) (float64, error) {
	num1, err1 := strconv.ParseFloat(first, 64)
	num2, err2 := strconv.ParseFloat(second, 64)
	if err1 != nil || err2 != nil {
		return 0, errors.New("некорректный ввод")
	}
	switch operand {
	case "+":
		return num1 + num2, nil
	case "-":
		return num1 - num2, nil
	case "*":
		return num1 * num2, nil
	case "/":
		if num2 == 0 {
			return 0, errors.New("делить на ноль нельзя")
		}
		return num1 / num2, nil
	default:
		return 0, errors.New("неизвестный операнд")
	}
}

func removeBrackets(arr []string) []string {
	result := []string{}
	for i := 0; i < len(arr); i++ {
		if i < len(arr)-2 && arr[i] == "(" && arr[i+2] == ")" {
			result = append(result, arr[i+1])
			i += 2
		} else {
			result = append(result, arr[i])
		}
	}
	return result
}

func FindPriorityOperand(split []string) ([]string, error) {
	var idx int = -1
	var val int = 0
	for len(split) != len(removeBrackets(split)) {
		split = removeBrackets(split)
	}
	for i := 0; i < len(split); i++ {
		curElement := split[i]
		if strings.Contains("*/", curElement) && val < 2 {
			idx = i
			val = 2
		}
		if strings.Contains("+-", curElement) && val < 1 {
			idx = i
			val = 1
		}
		if curElement == "(" {
			idx = -1
			val = 0
		}
		if curElement == ")" {
			break
		}
	}
	if idx == -1 {
		return split, nil
	}
	result, err := Operation(split[idx-1], split[idx], split[idx+1])
	if err != nil {
		return nil, err
	}
	temp := append(split[:idx-1], fmt.Sprintf("%.2f", result))
	split = append(temp, split[idx+2:]...)
	return FindPriorityOperand(split)
}

func Calc(expression string) (float64, error) {
	re := regexp.MustCompile(`-?\d+(\.\d*)?|[+\-*/()]`)
	split := re.FindAllString(expression, -1)
	if len(split) == 0 {
		return 0, errors.New("некорректный ввод")
	}
	split, err := FindPriorityOperand(split)
	if err != nil {
		return 0, err
	}
	if len(split) != 1 {
		return 0, errors.New("некорректный ввод")
	}
	result, err := strconv.ParseFloat(split[0], 64)
	if err != nil {
		return 0, errors.New("ошибка при получении ответа")
	}
	return result, nil
}
