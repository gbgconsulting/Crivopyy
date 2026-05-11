# Documentação — Crivopy

Sistema de triagem de currículos e documentos PDF com suporte a análise via IA (RAG).

---

## Índice

| Arquivo | Conteúdo |
|---|---|
| [arquitetura.md](./arquitetura.md) | Visão geral do projeto, stack, estrutura de apps e fluxo de dados |
| [models.md](./models.md) | Descrição de todos os models, campos, relacionamentos e valores de status |
| [urls.md](./urls.md) | Mapa completo de rotas do sistema |
| [design-system.md](./design-system.md) | Paleta de cores, tipografia, componentes e padrões de UI |
| [codigo.md](./codigo.md) | Convenções de código, padrões de views, forms, signals e segurança |
| [rag.md](./rag.md) | Como funciona o pipeline de análise com IA (RAG) |

---

## Setup rápido (Docker)

Não é necessário instalar Python na máquina host: o app e o Django rodam dentro dos containers.

**Pré-requisitos:** Docker e Docker Compose.

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd Crivopyy

# 2. Configurar variáveis (ou deixe o Makefile copiar o .env.example na primeira vez)
cp .env.example .env
# Edite .env (SECRET_KEY, OPENAI_API_KEY, etc.)

# 3. Subir PostgreSQL + aplicação
make up-build

# 4. (Opcional) Criar superusuário para o admin Django
make createsuperuser
```

A aplicação fica em `http://127.0.0.1:8000/` (porta configurável com `WEB_PORT` no ambiente do Compose).

### Comandos úteis (Makefile)

| Comando | Descrição |
|---------|-----------|
| `make up` / `make up-build` | Sobe os serviços (`up-build` reconstrói a imagem) |
| `make down` | Para e remove containers da stack |
| `make logs` | Acompanha logs do serviço `web` |
| `make migrate` | `migrate` dentro do container |
| `make shell` | Shell Django interativo |
| `make check` | `manage.py check` |
| `make createsuperuser` | Criar usuário admin |
| `make django CMD=...` | Qualquer subcomando, ex. `make django CMD=migrate` |

Todos esses comandos assumem que o container `web` está em execução (`make up`). O interpretador Python usado é o da imagem Docker, não o `python3` do host.

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
SECRET_KEY=sua-secret-key-aqui
DEBUG=True
OPENAI_API_KEY=sua-chave-openai  # necessário para o módulo RAG
```

Com Docker Compose, o banco padrão é o **PostgreSQL** do serviço `db`; as credenciais podem ser ajustadas via `POSTGRES_*` (veja `docker-compose.yml` e `.env.example`).

> Para desenvolvimento, o sistema funciona sem `OPENAI_API_KEY` exceto pelo módulo de análise RAG.
