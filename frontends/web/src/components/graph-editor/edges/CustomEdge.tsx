/**
 * CustomEdge Component
 * Custom edge component for relationships with type-based styling and arrow markers
 * 
 * **Validates: Requirements 1.2, 1.7**
 */

import { memo } from 'react';
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from 'reactflow';
import type { EdgeProps } from 'reactflow';
import type { Relationship } from '../GraphEditorContext';
import './CustomEdge.css';

/**
 * Relationship type definitions based on backend
 */
export type RelationshipType = 
  | 'CONTAINS'
  | 'DEPENDS_ON'
  | 'ASSIGNED_TO'
  | 'RELATES_TO'
  | 'IMPLEMENTS'
  | 'MITIGATES'
  | 'PREVIOUS'
  | 'SCHEDULED'
  | 'TO'
  | 'FOR'
  | 'REFINES'
  | 'CAN_OCCUR'
  | 'LEAD_TO';

/**
 * Edge styling configuration based on relationship type
 */
const EDGE_STYLES: Record<RelationshipType, { color: string; strokeWidth: number; strokeDasharray?: string }> = {
  CONTAINS: { color: '#3b82f6', strokeWidth: 2 }, // Blue - containment
  DEPENDS_ON: { color: '#ef4444', strokeWidth: 2, strokeDasharray: '5,5' }, // Red dashed - dependency
  ASSIGNED_TO: { color: '#10b981', strokeWidth: 2 }, // Green - assignment
  RELATES_TO: { color: '#6b7280', strokeWidth: 1.5 }, // Gray - general relation
  IMPLEMENTS: { color: '#8b5cf6', strokeWidth: 2 }, // Purple - implementation
  MITIGATES: { color: '#f59e0b', strokeWidth: 2 }, // Orange - mitigation
  PREVIOUS: { color: '#64748b', strokeWidth: 1, strokeDasharray: '2,2' }, // Slate dashed - version history
  SCHEDULED: { color: '#06b6d4', strokeWidth: 2 }, // Cyan - scheduling
  TO: { color: '#6b7280', strokeWidth: 1.5 }, // Gray - general direction
  FOR: { color: '#6b7280', strokeWidth: 1.5 }, // Gray - general purpose
  REFINES: { color: '#ec4899', strokeWidth: 2 }, // Pink - refinement
  CAN_OCCUR: { color: '#d97706', strokeWidth: 2.5 }, // Amber - FMEA risk occurrence
  LEAD_TO: { color: '#dc2626', strokeWidth: 2.5 }, // Crimson/Red - FMEA failure chain
};

/**
 * Get edge style based on relationship type
 */
function getEdgeStyle(type: string): { color: string; strokeWidth: number; strokeDasharray?: string } {
  const upperType = type.toUpperCase() as RelationshipType;
  return EDGE_STYLES[upperType] || { color: '#6b7280', strokeWidth: 1.5 };
}

/**
 * CustomEdge Component
 * Renders a styled edge with arrow marker based on relationship type
 */
export const CustomEdge = memo(({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data }: EdgeProps) => {
  const relationship = data?.relationship as Relationship | undefined;
  const relationshipType = relationship?.type || 'RELATES_TO';
  
  const style = getEdgeStyle(relationshipType);
  
  // Calculate bezier path for smooth curves
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Create unique marker ID for this edge type
  const markerId = `arrow-${relationshipType.toLowerCase()}`;

  // Handle mouse events for tooltip
  const handleMouseEnter = (event: React.MouseEvent) => {
    if (data?.onMouseEnter) {
      data.onMouseEnter(event, id);
    }
  };

  const handleMouseLeave = () => {
    if (data?.onMouseLeave) {
      data.onMouseLeave();
    }
  };

  return (
    <>
      {/* Define arrow marker in SVG defs */}
      <defs>
        <marker
          id={markerId}
          markerWidth="12"
          markerHeight="12"
          refX="10"
          refY="6"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path
            d="M 0 0 L 12 6 L 0 12 z"
            fill={style.color}
          />
        </marker>
      </defs>

      {/* Render the edge path */}
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: style.color,
          strokeWidth: style.strokeWidth,
          strokeDasharray: style.strokeDasharray,
        }}
        markerEnd={`url(#${markerId})`}
      />

      {/* Invisible wider path for easier hover detection */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={20}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{ cursor: 'pointer' }}
      />

      {/* Render edge label for CAN_OCCUR and LEAD_TO */}
      {(relationshipType === 'CAN_OCCUR' || relationshipType === 'LEAD_TO') && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              fontSize: 9,
              fontWeight: 600,
              color: style.color,
              backgroundColor: 'rgba(255,255,255,0.85)',
              padding: '1px 5px',
              borderRadius: 3,
              border: `1px solid ${style.color}`,
              pointerEvents: 'all',
              whiteSpace: 'nowrap',
            }}
            className="nodrag nopan"
          >
            {relationshipType}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

CustomEdge.displayName = 'CustomEdge';
