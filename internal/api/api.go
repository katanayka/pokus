package api

import (
	"encoding/json"
	"net/http"
	"peso/internal/math"
)

type CalculateRequest struct {
	Expression string `json:"expression"`
}

type SuccessResponse struct {
	Result float64 `json:"result"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

func CalculateHandler(w http.ResponseWriter, r *http.Request) {
	defer func() {
		if r := recover(); r != nil {
			sendErrorResponse(w, "Internal server error", http.StatusInternalServerError)
		}
	}()

	if r.Method != http.MethodPost {
		sendErrorResponse(w, "Method should be POST", http.StatusMethodNotAllowed)
		return
	}

	var req CalculateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendErrorResponse(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result, err := math.Calc(req.Expression)
	if err != nil {
		sendErrorResponse(w, err.Error(), http.StatusUnprocessableEntity)
		return
	}
	sendSuccessResponse(w, result)
}

func sendSuccessResponse(w http.ResponseWriter, result float64) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(SuccessResponse{Result: result})
}

func sendErrorResponse(w http.ResponseWriter, errorMsg string, statusCode int) {
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(ErrorResponse{Error: errorMsg})
}
