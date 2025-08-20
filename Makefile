.PHONY: help build up down logs clean test install-deps

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

poetry-upgrade:
	docker-compose run --rm document-api poetry update
	docker-compose run --rm data-store poetry update

poetry-lock:
	docker-compose run --rm document-api poetry lock
	docker-compose run --rm data-store poetry lock

build: ## Build all Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## Show logs from all services
	docker compose logs -f

clean: ## Stop services and remove volumes
	docker compose down -v
	docker system prune -f

test: ## Run the API test script
	python3 -m venv venv
	. venv/bin/activate && pip install requests && python3 test_api.py
