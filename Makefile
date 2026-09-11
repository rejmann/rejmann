.PHONY: svg ascii panel stats help debug-env debug-workflow debug-fetch setup up docker-build docker-debug docker-workflow docker-fetch
all: help
SHELL := /bin/bash

# Absolutely awesome: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

svg: ascii panel ## regenera os dois temas (arte ASCII + painel compartilhado)
	@true

ascii: ## regenera o bloco ASCII a partir de dark_mode.txt / light_mode.txt
	python3 cli/ascii_to_svg.py $(MODE)

panel: ## regenera o painel de infos a partir de panel.yaml (dark + light)
	python3 cli/panel_to_svg.py

stats: ## busca os números do GitHub, grava no panel.yaml e regenera os SVGs (precisa de ACCESS_TOKEN e USER_NAME)
	python3 cli/fetch_stats.py

debug-env: ## valida ACCESS_TOKEN e USER_NAME antes do debug local
	@if [ -f .env ]; then set -a && . ./.env && set +a; fi; \
	if [ -z "$${ACCESS_TOKEN:-}" ] || [ -z "$${USER_NAME:-}" ]; then \
		echo "Missing env vars: ACCESS_TOKEN and/or USER_NAME"; \
		echo "Create a .env file based on .env.example before running the workflow locally."; \
		exit 1; \
	fi; \
	echo "ACCESS_TOKEN: configured"; \
	echo "USER_NAME: $${USER_NAME}"

debug-workflow: debug-env ## executa o mesmo passo do workflow do GitHub Actions localmente
	@if [ -f .env ]; then set -a && . ./.env && set +a; fi; \
	python3 cli/today.py

debug-fetch: debug-env ## executa a coleta de dados local equivalente ao job de build
	@if [ -f .env ]; then set -a && . ./.env && set +a; fi; \
	python3 cli/fetch_stats.py

.env: ## cria um .env local a partir do exemplo
	cp .env.dist .env

setup: .env up ## setup do projeto local

up: ## constrói a imagem Docker do projeto
	docker compose up --build -d

docker-build: ## constrói a imagem Docker do projeto
	docker compose build --no-cache

docker-debug: ## abre um shell interativo dentro do container para debugar o workflow
	docker compose run --rm debug

docker-workflow: ## executa o workflow no container
	docker compose run --rm app

docker-fetch: ## executa a coleta de stats no container
	docker compose run --rm fetch
