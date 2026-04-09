# AI Features

RxD3 integrates AI capabilities through two main features: a teachable Skills system and a context-aware Chat interface.

## AI Skills

Skills are self-contained units of knowledge, rules, or behavioral guidance that can be taught to the AI. They are stored as `Skill` nodes in Neo4j and managed via a full CRUD API.

Each skill has a name, description, and content body. Skills can be toggled on/off — only enabled skills are injected into the AI's context when generating responses.

Use cases: project-specific rules, domain knowledge, coding standards, workflow guidance.

![Skills Management](pictures/Screenshot%20From%202026-03-15%2022-11-24.png)

## AI Chat

The chat interface provides a streaming conversation with a configurable AI provider (OpenAI, Anthropic, LM Studio, or custom). The backend builds a context prompt from:

- Enabled skills (via the KnowledgeStore)
- Project graph data from Neo4j
- Conversation history

Responses are streamed as Server-Sent Events for a responsive feel.

Configure the provider via environment variables (`AI_PROVIDER`, `AI_API_ENDPOINT`, `AI_MODEL_NAME`, `AI_API_KEY`).

![AI Chat](pictures/Screenshot%20From%202026-03-15%2022-11-07.png)

The AI is "Tool aware" - which means it can directly create nodes and/or relations for you:

![AI Tools](pictures/Screenshot%20From%202026-03-15%2022-19-23.png)

## GraphRAG Knowledge Base

GraphRAG transforms the Neo4j graph into a semantically queryable knowledge base. Instead of injecting a flat node list into the AI context, it uses vector embeddings and graph traversal to find the most relevant information for each query.

### How it works

1. **Embedding** — Mind node text (title + description + tags) is embedded via a configurable provider (OpenAI, LM Studio, custom). Vectors are stored directly on nodes and indexed with Neo4j's native vector index.
2. **Semantic search** — User queries are embedded and matched against the vector index using cosine similarity (configurable top-k and threshold).
3. **Graph traversal** — Seed nodes from semantic search are expanded via BFS up to a configurable depth, pulling in related nodes and relationships for richer context.
4. **Community detection** — Label Propagation (NetworkX) clusters the graph into communities. An AI-generated summary is stored per community for high-level reasoning.
5. **Context assembly** — The enhanced KnowledgeStore merges schema info, semantic hits, traversal context, and community summaries into a single prompt, respecting token limits.

### Retrieval modes

| Mode     | Behavior                                                  |
|----------|-----------------------------------------------------------|
| `auto`   | Classifies the query as local or global based on keywords |
| `local`  | Semantic search + neighbor traversal                      |
| `global` | Community summaries ranked by relevance                   |
| `hybrid` | Both local and global (70/30 token split)                 |

The mode selector appears in the chat interface when GraphRAG is enabled.

### Dashboard card

The Knowledge Base card on the Dashboard shows embedding/community status and provides buttons to trigger bulk embedding and community detection. Operations use in-memory locks (HTTP 409 if already running).

### API endpoints

All under `/api/v1/graphrag`, JWT-authenticated:

| Method | Path                     | Description                        |
|--------|--------------------------|------------------------------------|
| POST   | `/embeddings/generate`   | Bulk-embed all un-embedded nodes   |
| POST   | `/communities/detect`    | Run community detection + summaries|
| GET    | `/status`                | Node/embedding/community counts    |
| POST   | `/search`                | Standalone semantic search         |

### Feature gate

Set `GRAPHRAG_ENABLED=false` (default) to disable entirely — the system falls back to the original KnowledgeStore behavior with zero overhead.

### Chat history

Conversations are now persisted to `localStorage` and restored on page load. A "Clear History" button resets the conversation.

### GraphRAG Configuration

| Variable                          | Description                              | Default  |
|-----------------------------------|------------------------------------------|----------|
| `EMBEDDING_PROVIDER`              | Embedding provider type                  | `none`   |
| `EMBEDDING_API_ENDPOINT`          | Embedding API URL                        | —        |
| `EMBEDDING_API_KEY`               | Embedding API key (cloud providers)      | —        |
| `EMBEDDING_MODEL_NAME`            | Embedding model identifier               | —        |
| `EMBEDDING_DIMENSIONS`            | Vector dimensions                        | `1536`   |
| `GRAPHRAG_ENABLED`                | Enable GraphRAG features                 | `false`  |
| `GRAPHRAG_TOP_K`                  | Semantic search result count             | `10`     |
| `GRAPHRAG_SIMILARITY_THRESHOLD`   | Min cosine similarity for inclusion      | `0.7`    |
| `GRAPHRAG_TRAVERSAL_DEPTH`        | Max BFS hops from seed nodes             | `2`      |
| `GRAPHRAG_MAX_SUBGRAPH_NODES`     | Max nodes in traversal subgraph          | `50`     |
| `GRAPHRAG_DEFAULT_MODE`           | Default retrieval mode                   | `auto`   |
| `GRAPHRAG_COMMUNITY_SCHEDULE_HOURS` | Auto-detection interval (0 = manual)  | `0`      |

> **Docker note:** When running in Docker, use `http://host.docker.internal:1234/v1` for local LM Studio endpoints (not `localhost`).

## Configuration

Local LLM's can be used via lm-studio

| Variable               | Description                          | Example                          |
|------------------------|--------------------------------------|----------------------------------|
| `AI_PROVIDER`          | Provider type                        | `openai`, `anthropic`, `lm-studio`, `none` |
| `AI_API_ENDPOINT`      | API endpoint URL                     | `http://localhost:1234/v1`       |
| `AI_API_KEY`           | API key (required for cloud providers) | `sk-...`                       |
| `AI_MODEL_NAME`        | Model identifier                     | `gpt-4`, `claude-3-sonnet-20240229` |
| `AI_REQUEST_TIMEOUT`   | Request timeout in seconds           | `60`                             |
| `AI_MAX_CONTEXT_TOKENS`| Max tokens for project context       | `8000`                           |
