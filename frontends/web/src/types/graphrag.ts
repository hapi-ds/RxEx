/**
 * TypeScript types for GraphRAG knowledge base API.
 *
 * Mirrors the backend Pydantic schemas in backend/src/schemas/graphrag.py.
 */

export interface KnowledgeBaseStatus {
  total_nodes: number;
  embedded_nodes: number;
  community_count: number;
  last_embedding_sync: string | null;
  last_community_detection: string | null;
  graphrag_enabled: boolean;
}

export type RetrievalMode = 'auto' | 'local' | 'global' | 'hybrid';

export interface SemanticSearchResult {
  uuid: string;
  title: string;
  description: string | null;
  mind_type: string;
  tags: string[] | null;
  score: number;
}

export interface SemanticSearchResponse {
  results: SemanticSearchResult[];
  query_embedding_time_ms: number;
  search_time_ms: number;
}

export interface OperationResponse {
  status: string;
  message: string;
  details: Record<string, unknown> | null;
}
