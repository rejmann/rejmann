.PHONY: help svg ascii panel stats setup up docker-own-repos
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

.env: ## cria .env a partir de .env.example (não sobrescreve um .env existente)
	@test -f .env || cp .env.example .env

setup: .env ## primeira vez: cria o .env e sobe o ambiente Docker
	$(MAKE) up

up: ## builda e sobe os containers via docker compose
	docker compose up --build -d

update-panel: ## fetch -> panel.yaml -> SVGs no container, de verdade, mas só com seus repos próprios (sem colaborador/org)
	docker compose run --rm -e LOC_AFFILIATIONS=OWNER app
