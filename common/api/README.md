# common/api

Thin clients for OpenAI-compatible endpoints, shared by all baselines. Configured through `.env` (see `.env.example`).

| Client | Endpoint | Purpose |
|---|---|---|
| chat | `LLM_API_*` / `JUDGE_API_*`, `/chat/completions` | answering and memory construction, with token / call accounting per operation (ingest vs. QA, and per memory op) |
| embedding | `EMB_API_*`, `/embeddings` | shared embedding model |
| rerank | `RERANK_API_*`, `/rerank` (not OpenAI format) | shared reranker, for baselines that use one |

Baselines whose official code hard-codes its own LLM / embedding client get a shim in their `harness/` that routes calls through these clients.

TODO
