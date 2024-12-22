# Calc API

This project implements a web service for evaluating arithmetic expressions.

## Starting the service
1. Install [Go](https://go.dev/dl/)
2. Clone repo:
   ```
    git clone https://github.com/katanayka/pokus.git
   ```
3. Run server:
   ```
    go run .\cmd\app\main.go
   ```
4. The service will be available at: http://localhost:8080/api/v1/calculate

## How to use

### Example (insert this to git bash)
```bash
curl --location 'http://localhost:8080/api/v1/calculate' \
--header 'Content-Type: application/json' \
--data '{
  "expression": "MATH EXPRESSION"
}'
```
The math expression must be of the form 1 - 1 * (1 * 1 / 1 + 1) (with spaces)

## Scenarios

| **Request Method** | **Endpoint** | **Request Body**                                           | **Response Body**                                    | **HTTP Status Code** |
|--------------------|--------------|------------------------------------------------------------|------------------------------------------------------|----------------------|
| POST               | `/api/v1/calculate`  | `{ "expression": "2 + 2" }`                               | `{ "result": 4 }`                                    | 200 OK               |
| POST               | `/api/v1/calculate`  | `{ "expression": "2 / 0" }`                               | `{ "error":"division by zero" }`                     | 422 Unprocessable Entity |
| POST               | `/api/v1/calculate`  | `{ "expression": "invalid expression" }`                  | `{ "error": "Invalid expression" }`                  | 422 Unprocessable Entity |
| POST               | `/api/v1/calculate`  | `{ "expression": }`                                       | `{ "error": "Invalid request body" }`                | 400 Bad Request      |
| POST               | `/api/v1/calculate`  | `non-json string`                                         | `{ "error": "Invalid request body" }`                | 400 Bad Request      |
| GET                | `/api/v1/calculate`  | N/A                                                       | `{ "error":"Method should be POST" }`                | 405 Method Not Allowed |
