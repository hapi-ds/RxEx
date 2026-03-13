/**
 * SprintNode Component
 * Custom node component for Sprint mind type
 * 
 * **Validates: Requirements 1.1, 1.9**
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import type { Sprint } from '../../../types/generated';
import './BaseNode.css';

export interface SprintNodeData {
  mind: Sprint;
  isSelected: boolean;
}

/**
 * SprintNode Component
 * Displays a Sprint node with test_item attribute
 */
export const SprintNode = memo(({ data, selected }: NodeProps<SprintNodeData>) => {
  const { mind } = data;
  
  return (
    <div className={`base-node sprint-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} />
      
      <div className="node-header">
        <div className="node-type-badge">Sprint</div>
        <div className="node-status">{mind.status || 'draft'}</div>
      </div>
      
      <div className="node-content">
        <div className="node-title">{mind.title}</div>
        {mind.test_item !== undefined && (
          <div className="node-attribute">
            <span className="attribute-label">Test Item:</span>
            <span className="attribute-value">{mind.test_item}</span>
          </div>
        )}
      </div>
      
      <div className="node-footer">
        <div className="node-meta">v{mind.version}</div>
      </div>
      
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
});

SprintNode.displayName = 'SprintNode';
