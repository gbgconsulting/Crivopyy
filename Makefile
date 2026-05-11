# Desenvolvimento e Django sempre via Docker — não use python/python3 na máquina host.
COMPOSE_TOOLBOX := docker compose -f docker-compose.python-toolbox.yml
TOOLBOX_CONTAINER := crivopy-python313

.PHONY: build up up-build down logs shell migrate local ps createsuperuser check django restart
.PHONY: toolbox-up toolbox-down toolbox-bash toolbox-run toolbox-manage

build:
	docker compose build

# Sobe postgres + web (Gunicorn 0.0.0.0:8000; navegador: http://127.0.0.1:${WEB_PORT:-8000})
up:
	@test -f .env || cp .env.example .env
	docker compose up -d

# Reconstrói a imagem e sobe em seguida (útil após mudar requirements.txt)
up-build:
	@test -f .env || cp .env.example .env
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f web

# Requer `make up` com o container web rodando
shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

createsuperuser:
	docker compose exec web python manage.py createsuperuser

check:
	docker compose exec web python manage.py check

# Ex.: make django CMD=migrate
# Ex.: make django CMD="collectstatic --noinput"
django:
	docker compose exec web python manage.py $(CMD)

# Apenas Postgres (útil para dev híbrido — o app em si ainda seria no Docker com make up)
local:
	docker compose up -d db

ps:
	docker compose ps

restart:
	docker compose restart web

# Python 3.13 isolado (imagem oficial, sem pip install no Dockerfile). Container fica vivo com sleep infinity.
toolbox-up:
	$(COMPOSE_TOOLBOX) up -d

toolbox-down:
	$(COMPOSE_TOOLBOX) down

toolbox-bash:
	$(COMPOSE_TOOLBOX) exec -it python313 bash

# Requer toolbox-up. Servidor em 0.0.0.0:8000 (porta já mapeada no compose).
toolbox-run:
	docker exec -it -w /workspace $(TOOLBOX_CONTAINER) python manage.py runserver 0.0.0.0:8000

# Ex.: make toolbox-manage CMD=migrate
# Ex.: make toolbox-manage CMD="createsuperuser"
toolbox-manage:
	@test -n "$(CMD)" || (echo 'Uso: make toolbox-manage CMD=migrate (ou outro subcomando do manage.py)' && exit 1)
	docker exec -it -w /workspace $(TOOLBOX_CONTAINER) python manage.py $(CMD)
