# =============================================================================
# Financial IDR Pipeline - Makefile
# =============================================================================
# 
# Usage:
#   make help          - Show available commands
#   make build         - Build Docker image
#   make up            - Start containers
#   make down          - Stop containers
#   make logs          - View logs
#   make shell         - Open shell in container
#
# Author: Rajesh Kumar Gupta
# =============================================================================

.PHONY: help build up down logs shell test clean demo neo4j full

# Default target
.DEFAULT_GOAL := help

# Variables
IMAGE_NAME := financial-idr
IMAGE_TAG := latest
CONTAINER_NAME := financial-idr-api
DOCKER_COMPOSE := docker-compose

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help:
	@echo ""
	@echo "$(BLUE)Financial IDR Pipeline - Docker Commands$(NC)"
	@echo "=========================================="
	@echo ""
	@echo "$(GREEN)Build Commands:$(NC)"
	@echo "  make build        Build Docker image"
	@echo "  make rebuild      Rebuild without cache"
	@echo ""
	@echo "$(GREEN)Run Commands:$(NC)"
	@echo "  make up           Start API server"
	@echo "  make up-neo4j     Start with Neo4j database"
	@echo "  make up-full      Start all services"
	@echo "  make down         Stop all containers"
	@echo "  make restart      Restart containers"
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@echo "  make demo         Run demo inside container"
	@echo "  make shell        Open shell in container"
	@echo "  make logs         View container logs"
	@echo "  make test         Run tests"
	@echo ""
	@echo "$(GREEN)Maintenance Commands:$(NC)"
	@echo "  make clean        Remove containers and images"
	@echo "  make clean-all    Remove everything including volumes"
	@echo "  make status       Show container status"
	@echo ""

# -----------------------------------------------------------------------------
# Build Commands
# -----------------------------------------------------------------------------
build:
	@echo "$(BLUE)Building Docker image...$(NC)"
	$(DOCKER_COMPOSE) build

rebuild:
	@echo "$(BLUE)Rebuilding Docker image (no cache)...$(NC)"
	$(DOCKER_COMPOSE) build --no-cache

# -----------------------------------------------------------------------------
# Run Commands
# -----------------------------------------------------------------------------
up:
	@echo "$(GREEN)Starting Financial IDR API...$(NC)"
	$(DOCKER_COMPOSE) up -d financial-idr
	@echo "$(GREEN)API available at http://localhost:5000$(NC)"

up-neo4j:
	@echo "$(GREEN)Starting Financial IDR with Neo4j...$(NC)"
	$(DOCKER_COMPOSE) --profile neo4j up -d
	@echo "$(GREEN)API available at http://localhost:5000$(NC)"
	@echo "$(GREEN)Neo4j Browser at http://localhost:7474$(NC)"

up-full:
	@echo "$(GREEN)Starting all services...$(NC)"
	$(DOCKER_COMPOSE) --profile full up -d
	@echo "$(GREEN)All services started!$(NC)"

down:
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) --profile full down

restart: down up
	@echo "$(GREEN)Containers restarted!$(NC)"

# -----------------------------------------------------------------------------
# Development Commands
# -----------------------------------------------------------------------------
demo:
	@echo "$(BLUE)Running demo...$(NC)"
	docker exec -it $(CONTAINER_NAME) python main.py --demo

shell:
	@echo "$(BLUE)Opening shell...$(NC)"
	docker exec -it $(CONTAINER_NAME) /bin/bash

logs:
	$(DOCKER_COMPOSE) logs -f financial-idr

logs-all:
	$(DOCKER_COMPOSE) --profile full logs -f

test:
	@echo "$(BLUE)Running tests...$(NC)"
	docker exec -it $(CONTAINER_NAME) pytest tests/ -v

# -----------------------------------------------------------------------------
# Status Commands
# -----------------------------------------------------------------------------
status:
	@echo "$(BLUE)Container Status:$(NC)"
	$(DOCKER_COMPOSE) --profile full ps

health:
	@echo "$(BLUE)Health Check:$(NC)"
	@curl -s http://localhost:5000/api/health | python -m json.tool || echo "$(RED)API not responding$(NC)"

# -----------------------------------------------------------------------------
# Cleanup Commands
# -----------------------------------------------------------------------------
clean:
	@echo "$(YELLOW)Cleaning up containers and images...$(NC)"
	$(DOCKER_COMPOSE) --profile full down --rmi local
	docker image prune -f

clean-all:
	@echo "$(RED)Removing everything including volumes...$(NC)"
	$(DOCKER_COMPOSE) --profile full down --rmi all --volumes
	docker system prune -f

# -----------------------------------------------------------------------------
# Quick Start
# -----------------------------------------------------------------------------
quick-start: build up
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)Financial IDR Pipeline is ready!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "API Endpoint: http://localhost:5000"
	@echo "Health Check: http://localhost:5000/api/health"
	@echo ""
	@echo "Run 'make demo' to see a demonstration"
	@echo "Run 'make logs' to view logs"
	@echo "Run 'make shell' to access the container"
	@echo ""
