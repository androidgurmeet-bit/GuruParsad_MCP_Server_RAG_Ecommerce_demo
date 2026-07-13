# Ecommerce MCP RAG Agent

A FastAPI service that combines **Model Context Protocol (MCP)** product tools with a local **RAG** pipeline for ecommerce Q&A.

## Features

- **MCP tools** — `list_products`, `get_product`, `search_products` (RAM/spec-aware search)
- **RAG pipeline** — FAISS + sentence-transformers over product catalog text
- **LangGraph agent** — routes product queries to MCP tools and policy/spec questions to RAG
- **REST API** — `/query`, `/products/{id}`, `/health`

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Ollama](https://ollama.com/) with `qwen3:1.7b` model pulled locally

## Setup

```bash
# Install dependencies
uv sync

# Pull the LLM model
ollama pull qwen3:1.7b

# Optional: copy and configure environment variables
cp .env.example .env
```

## Run

```bash
uv run uvicorn main:app --reload --port 8000
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health and version |
| `/query` | POST | Natural-language query (`{"query": "..."}`) |
| `/products/{id}` | GET | Product details by ID |

### Example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show me phones with 8gb ram"}'
```

## Project layout

```
app/                  # RAG, embeddings, product search helpers
data/product.json     # Product catalog
mcp_server_fastmcp.py # MCP stdio server (product tools)
main.py               # FastAPI app + agent orchestration
```

See [RAG_MCP_PIPELINE_FLOW.md](./RAG_MCP_PIPELINE_FLOW.md) for architecture details.
