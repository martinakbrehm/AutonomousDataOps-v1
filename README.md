# Autonomous DataOps Multi-Agent System / Sistema Multi-Agente DataOps
# AutonomiDB: Autonomous DataOps Engine

Construí este projeto para automatizar pipelines de limpeza, validação e transformação de dados com agentes autônomos que consultam memória (RAG) e, quando necessário, geram e executam código de transformação.

Resumo objetivo
- Recebe datasets (CSV/Excel), decide um plano de ação (limpeza → qualidade → transformação) usando um `Planner` que pode consultar um LLM, aplica passos por agentes especializados e guarda rastros em uma memória SQL + vetor quando aplicável.
- Entrega: dados limpos/transformados + sumário de qualidade e logs de execução que servem para auditoria e iteração.

Por que isso importa
- Reduz trabalho manual repetitivo em pipelines de ingestão de dados e acelera iterações: planificação automática, validação e geração de código tornam operações de preparação de dados mais previsíveis e auditáveis.

O que acontece quando você roda
- Upload de um CSV pelo endpoint `/run` ou execução via CLI `autodops run-pipeline`.
- O `PlannerAgent` produz um plano (JSON) — preferencialmente via LLM validado — ou usa uma regra fallback.
- Cada passo é executado pelo Orchestrator: `DataProcessingAgent` (clean/transform), `DataQualityAgent` (checks), `CodeGenAgent` (gera código seguro quando necessário) e `InsightAgent` (resume resultados).
- Logs/Issues são persistidos em `SQLMemory` (SQLite por padrão, Postgres em produção) e métricas expostas em `/metrics`.

Arquitetura (visão prática)
- Entrypoints
	- API: `api/main.py` (FastAPI) — upload de dataset, autenticação por `x-api-key`, validações e orquestração.
	- CLI: `autodops` — `serve` e `run-pipeline` para uso local.
- Padrões e fluxos
	- ETL orientado a passos: planejamento → execução por agentes → resumo/inspeção.
	- Observability: Prometheus metrics + OpenTelemetry tracing (console por padrão; OTLP configurável).
	- Persistência: `SQLMemory` (SQLAlchemy) para logs/issues; `VectorStore` (FAISS) opcional para RAG.
- Decisões técnicas relevantes
	- LLMs são acessados via `LLMAdapter` com um registro de providers (mock/http). Respostas do LLM são validadas por `tools/llm_validator.py` (JSON schema + blacklist) para evitar comandos perigosos e formatos inválidos.
	- Código gerado é validado e executado em um `venv` temporário (`tools/executor.py`) — trade-off pragmático entre isolamento e simplicidade. Para produção, recomendo contêiner por job.
	- Projeto empacotado (`pyproject.toml`) e containerizado com `Dockerfile` multi-stage e usuário não-root; `docker-compose.yml` provê stack local (app, redis, postgres, prometheus).

Tecnologias (com contexto)
- Python 3.11: linguagem principal, produtividade e ecossistema de bibliotecas.
- FastAPI + Uvicorn: API rápida, schema-driven e compatível com TestClient para integração contínua.
- SQLAlchemy: abstração DB; `DATABASE_URL` detecta Postgres para produção e SQLite para desenvolvimento.
- Redis (opcional): rate-limiting; fallback em memória para ambientes sem Redis.
- FAISS + sentence-transformers (opcional): embeddings e RAG — mantido como extras por peso e CI.
- OpenTelemetry + Prometheus: métricas e traces para observability; pronto para exportadores OTLP.
- pytest + fakeredis: testes unitários e integração com mocks para dependências externas.

Estrutura do repositório
- `api/` — FastAPI app e endpoints (autenticação, upload, run).
- `agents/` — implementações dos agentes: `planner_agent.py`, `data_processing_agent.py`, `data_quality_agent.py`, `codegen_agent.py`, `insight_agent.py`.
- `tools/` — helpers: IO, DB helpers, `executor.py` (venv runner), `external_api.py` (providers), `llm_validator.py`, `security.py`.
- `memory/` — `sql_memory.py` (SQLAlchemy wrapper) e `vector_store.py` (FAISS wrapper).
- `pipelines/` — `orchestrator.py` e `etl_pipeline.py` (constrói sistema e executa planos).
- `tests/` — unitários e integrações: CLI, pipeline, LLM behavior, segurança.
- `sql/migrations/` — migration inicial para Postgres (logs + issues).
- `Dockerfile`, `docker-compose.yml`, `.github/workflows/` — containerização e CI.

Como rodar (rápido, profissional)
1) Preparar ambiente

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows PowerShell
pip install -e .
cp .env.example .env
# editar .env: defina APP_API_KEY; para Postgres local, ajuste DATABASE_URL
```

2) Desenvolvimento rápido (sem containers)

```bash
autodops serve --reload
# abrir http://localhost:8000/docs e usar /run (headers: x-api-key)
```

3) Stack local com Postgres/Redis/Prometheus

```bash
run_local.bat   # Windows (ou ./run_local.sh no Unix)
# acessa app em :8000, Prometheus em :9090
```

4) Testes

```bash
# AutonomiDB — Engine Autonomous DataOps

Construí este projeto para automatizar pipelines de preparação de dados: limpeza, verificação de qualidade e transformações dirigidas por agentes. O sistema combina regras, memória consultável e, quando útil, suporte a modelos generativos controlados para planejar passos e gerar trechos de código seguros.

Resumo objetivo
- Entrada: conjuntos de dados tabulares (CSV/Excel).
- Saída: dados limpos/transformados, relatório de qualidade e trilha de execução (logs/issues) para auditoria.

Valor prático
- Reduz tempo manual em pipelines de ingestão e preparação, padroniza correções e documenta decisões de transformação para equipes de dados.

Fluxo operacional (o que acontece ao rodar)
- Cliente envia um arquivo via endpoint `/run` ou usa `autodops run-pipeline`.
- O `PlannerAgent` tenta obter um plano (JSON) via `LLMAdapter` — a saída do LLM é validada por `tools/llm_validator.py`. Se inválida, o planner cai para um planner baseado em regras.
- O `Orchestrator` executa cada passo com agentes especializados:
	- `DataProcessingAgent`: limpeza e transformações padrão (Pandas).
	- `DataQualityAgent`: checagens e detecção de anomalias.
	- `CodeGenAgent`: gera código quando necessário; código passa por validação e é executado em `venv` temporário.
	- `InsightAgent`: sumariza resultados e populates o `VectorStore` opcional.
- Logs e issues são persistidos em `SQLMemory` e métricas são expostas em `/metrics`.

Arquitetura e decisões técnicas
- Entradas: API FastAPI (`api/main.py`) e CLI (`autodops.cli`).
- Memória: `SQLMemory` (SQLAlchemy) para logs/issues; `VectorStore` (FAISS) como opcional para RAG.
- LLMs: abstração via `LLMAdapter` com registry de providers. Uso seguro do LLM com validação de schema e blacklist para mitigar respostas malformadas ou perigosas.
- Execução de código: válida antes de rodar; isolamento pragmático via venv temporário (trade-off entre segurança e complexidade). Para ambientes sensíveis recomendo execução em contêiner isolado por job.
- Observability: Prometheus para métricas e OpenTelemetry para tracing — arquitetura pensada para integração com OTLP/Grafana.

Tecnologias (por que foram escolhidas)
- Python 3.11 — produtividade e compatibilidade com bibliotecas de dados.
- FastAPI + Uvicorn — desempenho, documentação automática e facilidade de testes.
- SQLAlchemy — compatibilidade multi-DB; detecta `DATABASE_URL` para rodar com Postgres em produção.
- Redis — opcional para rate-limiting; fallback em memória implementado para simplicidade em dev.
- FAISS (opcional) — embeddings locais; deixado como extra por custo de dependências.
- OpenTelemetry + Prometheus — prontas para observability corporativa.

Estrutura do projeto (visão rápida)
- `api/` — endpoints, validação de upload e integração com Orchestrator.
- `agents/` — componentes que implementam responsabilidades claras (planner, processing, quality, codegen, insight).
- `tools/` — utilitários: IO, executor (venv), providers LLM, validação e segurança.
- `memory/` — `sql_memory.py` (SQLAlchemy) e `vector_store.py` (FAISS wrapper).
- `pipelines/` — orquestração e construção do sistema.
- `tests/` — cobertura unitária e de integração (incluindo testes LLM e Postgres em CI).

Como rodar (passos precisos)
1) Ambiente local (venv)

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows PowerShell
pip install -e .
copy .env.example .env     # Windows
# editar .env: definir APP_API_KEY e, opcionalmente, DATABASE_URL
```

2) Rodar rápido para desenvolvimento

```bash
autodops serve --reload
# abrir http://localhost:8000/docs e usar /run (header: x-api-key)
```

3) Rodar stack local (Postgres + Redis + Prometheus)

```bash
run_local.bat   # Windows
./run_local.sh  # Unix
```

4) Testes

```bash
pytest -q
```

Pontos fortes técnicos (por que interessa a recrutadores)
- Separação clara de responsabilidades (agents) que facilita manutenção e testes jurídicos.
- Validação em camadas para LLMs e execução de código com mitigação de riscos.
- CI configurado para testar com SQLite e Postgres — demonstra preocupação com parity entre dev/prod.
- Packaging e Docker multi-stage com usuário não-root, prontos para demonstrar entregáveis reais.

Limitações técnicas (seja honesto)
- Isolamento do executor: `venv` não é suficiente para código arbitrário; é um ponto de atenção para produção.
- Dependências pesadas de ML (FAISS, transformers) estão separadas como extras e não são testadas no pipeline principal.
- Migração de esquema: atualmente aplicada de forma simples; para evolução usar Alembic.

Próximos passos realistas
1. Integrar Alembic e rodar migrações controladas no CI antes dos testes.
2. Migrar a execução de código para contêineres por job (limitar CPU/mem/tempo).
3. Provisionar secrets via um vault e detalhar runbooks de deploy para staging/prod.
- Abordagem segura e pragmática com validações e fallback, evitando dependência cega de modelos generativos.
- Estrutura preparada para demonstração: instalação, testes e execução com Postgres local via docker-compose.

Se quiser, eu crio o script de demonstração e adiciono um badge de CI no topo do README.

