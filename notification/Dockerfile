FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
RUN go build -o /out/notify

FROM alpine:3.19
COPY --from=build /out/notify /notify
EXPOSE 8081
CMD ["/notify"]
