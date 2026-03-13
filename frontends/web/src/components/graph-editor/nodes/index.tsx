/**
 * Custom Node Components
 * Exports all custom node types and nodeTypes configuration for react-flow
 * 
 * **Validates: Requirements 1.1, 1.9**
 */

import type { NodeTypes } from 'reactflow';
import { ProjectNode } from './ProjectNode';
import { TaskNode } from './TaskNode';
import { CompanyNode } from './CompanyNode';
import { DepartmentNode } from './DepartmentNode';
import { EmailNode } from './EmailNode';
import { KnowledgeNode } from './KnowledgeNode';
import { AcceptanceCriteriaNode } from './AcceptanceCriteriaNode';
import { RiskNode } from './RiskNode';
import { FailureNode } from './FailureNode';
import { RequirementNode } from './RequirementNode';
import { ResourceNode } from './ResourceNode';
import { JournalentryNode } from './JournalentryNode';
import { BookingNode } from './BookingNode';
import { AccountNode } from './AccountNode';
import { ScheduleHistoryNode } from './ScheduleHistoryNode';
import { ScheduledTaskNode } from './ScheduledTaskNode';
import { SprintNode } from './SprintNode';

/**
 * Node types configuration for react-flow
 * Maps mind type names to their custom node components
 */
export const nodeTypes: NodeTypes = {
  Project: ProjectNode,
  Task: TaskNode,
  Company: CompanyNode,
  Department: DepartmentNode,
  Email: EmailNode,
  Knowledge: KnowledgeNode,
  AcceptanceCriteria: AcceptanceCriteriaNode,
  Risk: RiskNode,
  Failure: FailureNode,
  Requirement: RequirementNode,
  Resource: ResourceNode,
  Journalentry: JournalentryNode,
  Booking: BookingNode,
  Sprint: SprintNode,
  Account: AccountNode,
  ScheduleHistory: ScheduleHistoryNode,
  ScheduledTask: ScheduledTaskNode,
};

/**
 * Node color configuration
 * Maps mind type names to their display colors
 */
export const nodeColors: Record<string, string> = {
  Project: '#3b82f6',
  Task: '#10b981',
  Company: '#8b5cf6',
  Department: '#06b6d4',
  Email: '#f59e0b',
  Knowledge: '#ec4899',
  AcceptanceCriteria: '#14b8a6',
  Risk: '#ef4444',
  Failure: '#dc2626',
  Requirement: '#6366f1',
  Resource: '#84cc16',
  Journalentry: '#a855f7',
  Booking: '#f97316',
  Sprint: '#22c55e',
  Account: '#059669',
  ScheduleHistory: '#64748b',
  ScheduledTask: '#0891b2',
};

// Export individual components
export {
  ProjectNode,
  TaskNode,
  CompanyNode,
  DepartmentNode,
  EmailNode,
  KnowledgeNode,
  AcceptanceCriteriaNode,
  RiskNode,
  FailureNode,
  RequirementNode,
  ResourceNode,
  JournalentryNode,
  BookingNode,
  AccountNode,
  ScheduleHistoryNode,
  ScheduledTaskNode,
  SprintNode,
};
