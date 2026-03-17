/**
 * TypeScript type definitions for the FastAPI Neo4j Multi-Frontend System
 * These types match the backend Pydantic models and API contracts
 */

/**
 * User entity representing a registered user in the system
 */
export interface User {
  id: string;
  email: string;
  fullname: string;
}

/**
 * Post entity representing a user-created post
 */
export interface Post {
  id: string;
  title: string;
  content: string;
  date_created: string;
  date_updated: string;
  tags: string[];
}

/**
 * Request payload for creating a new post
 */
export interface PostCreate {
  title: string;
  content: string;
  tags: string[];
}

/**
 * Request payload for updating an existing post
 */
export interface PostUpdate {
  title: string;
  content: string;
  tags: string[];
}

/**
 * JWT authentication token response from login endpoint
 */
export interface Token {
  access_token: string;
  type: string;
}

/**
 * Login credentials for authentication
 */
export interface LoginCredentials {
  username: string; // email
  password: string;
}

/**
 * WebSocket message types for real-time communication
 */
export interface WSMessage {
  type: 'message' | 'user_event';
  content?: string;
  sender?: string;
  event?: 'joined' | 'left';
  email?: string;
  timestamp: string;
}

/**
 * Relationship types for Mind Graph connections
 */
export type RelationshipType = 
  | 'PREVIOUS'
  | 'SCHEDULED'
  | 'CONTAINS'
  | 'PREDATES'
  | 'ASSIGNED_TO'
  | 'DEPENDS_ON'
  | 'RELATES_TO'
  | 'IMPLEMENTS'
  | 'MITIGATES'
  | 'TO'
  | 'FOR'
  | 'REFINES'
  | 'HAS_SCHEDULED'
  | 'CAN_OCCUR'
  | 'LEAD_TO';

/**
 * Relationship entity representing connections between Mind nodes
 */
export interface Relationship {
  id: string;
  type: RelationshipType;
  source: string; // UUID of source Mind
  target: string; // UUID of target Mind
  properties: Record<string, any>;
}


/** Skill summary for list views (excludes content) */
export interface Skill {
  uuid: string;
  name: string;
  description: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

/** Full skill detail including content */
export interface SkillDetail extends Skill {
  content: string;
}

/** Payload for creating a new skill */
export interface SkillCreate {
  name: string;
  description: string;
  content: string;
}

/** Payload for updating an existing skill */
export interface SkillUpdate {
  name: string;
  description: string;
  content: string;
}

/** Mind node as serialized in save file */
export interface MindExport {
  uuid: string;
  mind_type: string;
  title: string;
  version: number;
  created_at: string;
  updated_at: string;
  creator: string;
  status: string;
  description: string | null;
  tags: string[] | null;
  type_specific_attributes: Record<string, unknown>;
}

/** Relationship as serialized in save file */
export interface RelationshipExport {
  source_uuid: string;
  target_uuid: string;
  relationship_type: string;
  properties: Record<string, unknown>;
}

/** Post node as serialized in save file */
export interface PostExport {
  id: string;
  title: string;
  content: string;
  tags: string[];
  date_created: string;
  date_updated: string;
}

/** Structure of the save file JSON */
export interface SaveFileData {
  minds: MindExport[];
  relationships: RelationshipExport[];
  posts: PostExport[];
}

/** Response from the read endpoint */
export interface ReadResponse {
  minds_count: number;
  relationships_count: number;
  posts_count: number;
}

/** Response from the clear endpoint */
export interface ClearResponse {
  minds_deleted: number;
  relationships_deleted: number;
  posts_deleted: number;
}

/** Schedule history entry from the API */
export interface ScheduleHistory {
  uuid: string;
  schedule_id: string;
  scheduled_at: string;
  total_effort: number | null;
  total_cost: number | null;
  global_start: string | null;
  global_end: string | null;
  version: number;
}

/** Enriched scheduled task with original task info */
export interface ScheduledTaskEnriched {
  uuid: string;
  source_task_uuid: string;
  scheduled_start: string;
  scheduled_end: string;
  scheduled_duration: number;
  is_critical: boolean;
  slack_start: number | null;
  slack_end: number | null;
  base_cost: number | null;
  variable_cost: number | null;
  total_cost: number | null;
  task_title: string;
  task_type: string;
  hierarchy_level: number;
  predecessors: string[];
  progress: number;
  booked_hours: number;
}

/** Response from schedule creation */
export interface ScheduleCreateResponse {
  success: boolean;
  schedule_id: string;
  version: number;
  message: string;
}

/** Gantt chart component props */
export interface GanttChartProps {
  tasks: ScheduledTaskEnriched[];
  timeScale: 'weeks' | 'months' | 'quarters' | 'years';
  maxDepth: number;
  globalStart: string;
  globalEnd: string;
}

/** Burn-down chart data point */
export interface BurnDownPoint {
  sprint_number: number;
  sprint_label: string;
  ideal_remaining: number;
  actual_remaining: number;
}
