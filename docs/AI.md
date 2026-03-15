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
