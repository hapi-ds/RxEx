/**
 * Node Type Configuration
 * Defines attributes, validation rules, and metadata for each node type
 * 
 * **Validates: Requirements 4.5, 4.6**
 */

import type { NodeType } from '../../types/generated';
import {
  StatusEnum,
  PriorityEnum,
  SeverityEnum,
  ProbabilityEnum,
  ResourceType,
  AccountType,
  TaskType,
  RequirementType,
} from '../../types/generated';

export interface AttributeConfig {
  name: string;
  type: 'string' | 'number' | 'date' | 'datetime' | 'boolean' | 'enum' | 'array';
  required: boolean;
  readonly: boolean;
  validation?: {
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    enumValues?: string[];
  };
  label: string;
  placeholder?: string;
  helpText?: string;
}

export interface NodeTypeConfig {
  type: NodeType;
  label: string;
  attributes: AttributeConfig[];
}

// Base attributes common to all node types
const baseAttributes: AttributeConfig[] = [
  {
    name: 'uuid',
    type: 'string',
    required: true,
    readonly: true,
    label: 'UUID',
  },
  {
    name: 'title',
    type: 'string',
    required: true,
    readonly: false,
    validation: { minLength: 1, maxLength: 200 },
    label: 'Title',
    placeholder: 'Enter title',
  },
  {
    name: 'version',
    type: 'number',
    required: true,
    readonly: true,
    label: 'Version',
  },
  {
    name: 'created_at',
    type: 'datetime',
    required: true,
    readonly: true,
    label: 'Created At',
  },
  {
    name: 'updated_at',
    type: 'datetime',
    required: true,
    readonly: true,
    label: 'Updated At',
  },
  {
    name: 'creator',
    type: 'string',
    required: true,
    readonly: false,
    validation: { minLength: 1 },
    label: 'Creator',
    placeholder: 'Enter creator name',
  },
  {
    name: 'status',
    type: 'enum',
    required: false,
    readonly: false,
    validation: { enumValues: Object.values(StatusEnum) },
    label: 'Status',
  },
  {
    name: 'description',
    type: 'string',
    required: false,
    readonly: false,
    validation: { maxLength: 1000 },
    label: 'Description',
    placeholder: 'Enter description',
  },
  {
    name: 'tags',
    type: 'array',
    required: false,
    readonly: false,
    label: 'Tags',
    placeholder: 'Add tag',
  },
];

// Node type configurations
export const NODE_TYPE_CONFIGS: Record<NodeType, NodeTypeConfig> = {
  Project: {
    type: 'Project',
    label: 'Project',
    attributes: [
      ...baseAttributes,
      {
        name: 'start_date',
        type: 'date',
        required: true,
        readonly: false,
        label: 'Start Date',
      },
      {
        name: 'end_date',
        type: 'date',
        required: true,
        readonly: false,
        label: 'End Date',
      },
      {
        name: 'budget',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Budget',
        placeholder: 'Enter budget amount',
      },
    ],
  },

  Task: {
    type: 'Task',
    label: 'Task',
    attributes: [
      ...baseAttributes,
      {
        name: 'priority',
        type: 'enum',
        required: true,
        readonly: false,
        validation: { enumValues: Object.values(PriorityEnum) },
        label: 'Priority',
      },
      {
        name: 'due_date',
        type: 'date',
        required: false,
        readonly: false,
        label: 'Due Date',
      },
      {
        name: 'effort',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Effort (hours)',
        placeholder: 'Enter effort in hours',
      },
      {
        name: 'duration',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Duration (days)',
        placeholder: 'Enter duration in days',
      },
      {
        name: 'length',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Length (days)',
        placeholder: 'Enter length in days',
      },
      {
        name: 'task_type',
        type: 'enum',
        required: false,
        readonly: false,
        validation: { enumValues: Object.values(TaskType) },
        label: 'Task Type',
      },
      {
        name: 'phase_number',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Phase Number',
      },
      {
        name: 'target_date',
        type: 'date',
        required: false,
        readonly: false,
        label: 'Target Date',
      },
      {
        name: 'completion_percentage',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0, max: 100 },
        label: 'Completion %',
        placeholder: 'Enter percentage (0-100)',
      },
    ],
  },

  Company: {
    type: 'Company',
    label: 'Company',
    attributes: [
      ...baseAttributes,
      {
        name: 'industry',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Industry',
        placeholder: 'Enter industry',
      },
      {
        name: 'size',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Size (employees)',
        placeholder: 'Enter number of employees',
      },
      {
        name: 'founded_date',
        type: 'date',
        required: false,
        readonly: false,
        label: 'Founded Date',
      },
    ],
  },

  Department: {
    type: 'Department',
    label: 'Department',
    attributes: [
      ...baseAttributes,
      {
        name: 'department_code',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Department Code',
        placeholder: 'Enter department code',
      },
      {
        name: 'manager',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Manager',
        placeholder: 'Enter manager name',
      },
    ],
  },

  Email: {
    type: 'Email',
    label: 'Email',
    attributes: [
      ...baseAttributes,
      {
        name: 'sender',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Sender',
        placeholder: 'Enter sender email',
      },
      {
        name: 'recipients',
        type: 'array',
        required: true,
        readonly: false,
        label: 'Recipients',
        placeholder: 'Add recipient email',
      },
      {
        name: 'subject',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Subject',
        placeholder: 'Enter subject',
      },
      {
        name: 'sent_at',
        type: 'datetime',
        required: true,
        readonly: true,
        label: 'Sent At',
      },
    ],
  },

  Knowledge: {
    type: 'Knowledge',
    label: 'Knowledge',
    attributes: [
      ...baseAttributes,
      {
        name: 'category',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Category',
        placeholder: 'Enter category',
      },
      {
        name: 'content',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Content',
        placeholder: 'Enter content',
      },
    ],
  },

  AcceptanceCriteria: {
    type: 'AcceptanceCriteria',
    label: 'Acceptance Criteria',
    attributes: [
      ...baseAttributes,
      {
        name: 'criteria_text',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Criteria Text',
        placeholder: 'Enter criteria',
      },
      {
        name: 'verification_method',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Verification Method',
        placeholder: 'Enter verification method',
      },
      {
        name: 'verification_status',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Verification Status',
        placeholder: 'Enter status',
      },
    ],
  },

  Risk: {
    type: 'Risk',
    label: 'Risk',
    attributes: [
      ...baseAttributes,
      {
        name: 'severity',
        type: 'number',
        required: true,
        readonly: false,
        validation: { min: 1, max: 10 },
        label: 'Severity',
        placeholder: 'Enter severity (1-10)',
      },
      {
        name: 'probability',
        type: 'enum',
        required: true,
        readonly: false,
        validation: { enumValues: Object.values(ProbabilityEnum) },
        label: 'Probability',
      },
      {
        name: 'mitigation_plan',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Mitigation Plan',
        placeholder: 'Enter mitigation plan',
      },
      {
        name: 'acceptable_limit',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Acceptable Limit',
        placeholder: 'Enter acceptable risk threshold',
      },
    ],
  },

  Failure: {
    type: 'Failure',
    label: 'Failure',
    attributes: [
      ...baseAttributes,
      {
        name: 'failure_mode',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Failure Mode',
        placeholder: 'Enter failure mode',
      },
      {
        name: 'effects',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Effects',
        placeholder: 'Enter effects',
      },
      {
        name: 'causes',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Causes',
        placeholder: 'Enter causes',
      },
      {
        name: 'detection_method',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Detection Method',
        placeholder: 'Enter detection method',
      },
      {
        name: 'occurrence',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 1, max: 10 },
        label: 'Occurrence',
        placeholder: 'Enter occurrence rating (1-10)',
      },
      {
        name: 'detectability',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 1, max: 10 },
        label: 'Detectability',
        placeholder: 'Enter detectability rating (1-10)',
      },
    ],
  },

  Requirement: {
    type: 'Requirement',
    label: 'Requirement',
    attributes: [
      ...baseAttributes,
      {
        name: 'requirement_type',
        type: 'enum',
        required: true,
        readonly: false,
        validation: { enumValues: Object.values(RequirementType) },
        label: 'Requirement Type',
      },
      {
        name: 'content',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Content',
        placeholder: 'Enter requirement content',
      },
      {
        name: 'source',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Source',
        placeholder: 'Enter source',
      },
      {
        name: 'acceptance_criteria',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Acceptance Criteria',
        placeholder: 'Enter acceptance criteria',
      },
      {
        name: 'compliance_standard',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Compliance Standard',
        placeholder: 'Enter compliance standard',
      },
      {
        name: 'safety_critical',
        type: 'boolean',
        required: false,
        readonly: false,
        label: 'Safety Critical',
      },
    ],
  },

  Resource: {
    type: 'Resource',
    label: 'Resource',
    attributes: [
      ...baseAttributes,
      {
        name: 'email',
        type: 'string',
        required: false,
        readonly: false,
        label: 'Email',
        placeholder: 'Enter email',
      },
      {
        name: 'workinghours_max_per_week',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Max Hours/Week',
        placeholder: 'Enter max hours per week',
      },
      {
        name: 'workinghours_per_year',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Hours/Year',
        placeholder: 'Enter hours per year',
      },
      {
        name: 'efficiency',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0, max: 1 },
        label: 'Efficiency',
        placeholder: 'Enter efficiency (0-1)',
      },
      {
        name: 'hourly_rate',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Hourly Rate (EUR)',
        placeholder: 'Enter hourly rate',
      },
      {
        name: 'resource_type',
        type: 'enum',
        required: false,
        readonly: false,
        validation: { enumValues: Object.values(ResourceType) },
        label: 'Resource Type',
      },
    ],
  },

  Journalentry: {
    type: 'Journalentry',
    label: 'Journal Entry',
    attributes: [
      ...baseAttributes,
      {
        name: 'severity',
        type: 'enum',
        required: true,
        readonly: false,
        validation: { enumValues: Object.values(SeverityEnum) },
        label: 'Severity',
      },
    ],
  },

  Booking: {
    type: 'Booking',
    label: 'Booking',
    attributes: [
      ...baseAttributes,
      {
        name: 'hours_worked',
        type: 'number',
        required: true,
        readonly: false,
        validation: { min: 0 },
        label: 'Hours Worked',
        placeholder: 'Enter hours worked',
      },
      {
        name: 'booking_date',
        type: 'date',
        required: false,
        readonly: false,
        label: 'Booking Date',
      },
      {
        name: 'rate',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Rate (EUR/h)',
        placeholder: 'Enter hourly rate',
      },
      {
        name: 'amount',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Amount',
        placeholder: 'Enter amount',
      },
    ],
  },

  Sprint: {
    type: 'Sprint',
    label: 'Sprint',
    attributes: [
      ...baseAttributes,
      {
        name: 'sprint_number',
        type: 'number',
        required: true,
        readonly: false,
        validation: { min: 1 },
        label: 'Sprint Number',
        placeholder: 'Enter sprint number',
      },
      {
        name: 'start_date',
        type: 'date',
        required: true,
        readonly: false,
        label: 'Start Date',
      },
      {
        name: 'end_date',
        type: 'date',
        required: true,
        readonly: false,
        label: 'End Date',
      },
      {
        name: 'goal',
        type: 'string',
        required: false,
        readonly: false,
        validation: { maxLength: 500 },
        label: 'Goal',
        placeholder: 'Enter sprint goal',
      },
      {
        name: 'velocity',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Velocity',
        placeholder: 'Enter velocity',
      },
    ],
  },

  Account: {
    type: 'Account',
    label: 'Account',
    attributes: [
      ...baseAttributes,
      {
        name: 'account_type',
        type: 'enum',
        required: false,
        readonly: false,
        validation: { enumValues: Object.values(AccountType) },
        label: 'Account Type',
      },
    ],
  },

  ScheduleHistory: {
    type: 'ScheduleHistory',
    label: 'Schedule History',
    attributes: [
      ...baseAttributes.filter(attr => attr.name !== 'status'), // ScheduleHistory has status in different position
      {
        name: 'schedule_id',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Schedule ID',
        placeholder: 'Enter schedule ID',
      },
      {
        name: 'scheduled_at',
        type: 'datetime',
        required: false,
        readonly: true,
        label: 'Scheduled At',
      },
      {
        name: 'status',
        type: 'enum',
        required: false,
        readonly: false,
        validation: { enumValues: Object.values(StatusEnum) },
        label: 'Status',
      },
      {
        name: 'total_effort',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Total Effort',
        placeholder: 'Enter total effort',
      },
      {
        name: 'total_cost',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Total Cost',
        placeholder: 'Enter total cost',
      },
      {
        name: 'global_start',
        type: 'date',
        required: false,
        readonly: false,
        label: 'Global Start',
      },
      {
        name: 'global_end',
        type: 'date',
        required: false,
        readonly: false,
        label: 'Global End',
      },
    ],
  },

  ScheduledTask: {
    type: 'ScheduledTask',
    label: 'Scheduled Task',
    attributes: [
      ...baseAttributes,
      {
        name: 'source_task_uuid',
        type: 'string',
        required: true,
        readonly: false,
        validation: { minLength: 1 },
        label: 'Source Task UUID',
        placeholder: 'Enter source task UUID',
      },
      {
        name: 'scheduled_start',
        type: 'date',
        required: true,
        readonly: false,
        label: 'Scheduled Start',
      },
      {
        name: 'scheduled_end',
        type: 'date',
        required: true,
        readonly: false,
        label: 'Scheduled End',
      },
      {
        name: 'scheduled_duration',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Scheduled Duration',
        placeholder: 'Enter duration',
      },
      {
        name: 'scheduled_length',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Scheduled Length',
        placeholder: 'Enter length',
      },
      {
        name: 'is_critical',
        type: 'boolean',
        required: false,
        readonly: false,
        label: 'Is Critical',
      },
      {
        name: 'slack_start',
        type: 'number',
        required: false,
        readonly: false,
        label: 'Slack Start',
        placeholder: 'Enter slack start',
      },
      {
        name: 'slack_end',
        type: 'number',
        required: false,
        readonly: false,
        label: 'Slack End',
        placeholder: 'Enter slack end',
      },
      {
        name: 'base_cost',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Base Cost',
        placeholder: 'Enter base cost',
      },
      {
        name: 'variable_cost',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Variable Cost',
        placeholder: 'Enter variable cost',
      },
      {
        name: 'total_cost',
        type: 'number',
        required: false,
        readonly: false,
        validation: { min: 0 },
        label: 'Total Cost',
        placeholder: 'Enter total cost',
      },
    ],
  },
};

/**
 * Get configuration for a specific node type
 */
export function getNodeTypeConfig(nodeType: NodeType): NodeTypeConfig {
  return NODE_TYPE_CONFIGS[nodeType];
}

/**
 * Get attribute configuration for a specific attribute of a node type
 */
export function getAttributeConfig(
  nodeType: NodeType,
  attributeName: string
): AttributeConfig | undefined {
  const config = NODE_TYPE_CONFIGS[nodeType];
  return config.attributes.find(attr => attr.name === attributeName);
}
