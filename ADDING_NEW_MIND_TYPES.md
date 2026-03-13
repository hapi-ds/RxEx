# Adding New Mind Types - Complete Workflow

This document describes the complete workflow for adding a new mind type to the system.

## 🤖 AI Assistant Delegation Guide

**When you need to add a new Mind type or relationship**, you can delegate the work to an AI assistant by providing:

### Required Information:

1. **Mind Type Name**: The name of the new node type (e.g., "Sprint", "Epic", "TestRun")
2. **Attributes**: List of type-specific attributes with their types and constraints
3. **Purpose**: Brief description of what this mind type represents
4. **Relationships** (optional): Any new relationship types needed
5. **TODO Reference**: Point to relevant items in `TODOHK/List.md`

### Example Delegation Messages:

**Example 1: Simple Mind Type**
```
Please add a new Mind type called "Epic" with the following attributes:
- epic_number: int (required, min=1)
- story_points: int (optional, min=0)
- sprint_duration: int (optional, min=1, max=4, default=2)

This is for the "Project Planning (agile)" section in TODOHK/List.md.
Follow the checklist in ADDING_NEW_MIND_TYPES.md.
```

**Example 2: Complex Mind Type with Relationships**
```
Please add a new Mind type called "TestRun" for test management:

Attributes:
- test_type: enum (required, values: "validation", "verification", "integration")
- execution_date: date (required)
- status: enum (required, values: "pending", "running", "passed", "failed")
- test_results: string (optional, multiline)
- pass_rate: float (optional, min=0, max=100)

Relationships:
- Add "validates" relationship type (TestRun validates Requirement)
- Add "executes" relationship type (TestRun executes TestPlan)

This is for the "Test-Management" section in TODOHK/List.md.
Follow the checklist in ADDING_NEW_MIND_TYPES.md and update the TODO list when complete.
```

### What the AI Assistant Will Do:

The assistant will follow the complete 12-step checklist below:
1. Add backend Python class with proper validation
2. Register in backend models and service
3. Run type generation scripts
4. Create frontend React component
5. Register component and configure attributes
6. Test the integration
7. Update documentation and TODO list

---

## Overview

Adding a new mind type requires updates in both backend and frontend. The system has generation scripts to help automate some of this, but manual steps are still required.

## Step-by-Step Workflow

### 1. Backend: Define the Mind Type Class

**File**: `backend/src/models/mind_types.py`

Add your new mind type class:

```python
class Sprint(BaseMind):
    """Sprint Mind type for agile sprint management."""
    
    __primarylabel__: str = "Sprint"
    
    # Define required fields
    sprint_number: int = Field(..., ge=1, description="Sprint number")
    start_date: date = Field(..., description="Sprint start date")
    end_date: date = Field(..., description="Sprint end date")
    
    # Define optional fields
    goal: Optional[str] = Field(default=None, description="Sprint goal")
    velocity: Optional[float] = Field(default=None, ge=0, description="Sprint velocity")
```

**Key Points**:
- Inherit from `BaseMind`
- Set `__primarylabel__` to the PascalCase name
- Use Pydantic `Field()` for validation
- Required fields use `...`, optional fields use `default=None`
- Add field validators if needed (see other examples)

### 2. Backend: Register in Models Init

**File**: `backend/src/models/__init__.py`

Add import and export:

```python
from .mind_types import (
    # ... existing imports
    Sprint,  # Add this
)

__all__ = [
    # ... existing exports
    "Sprint",  # Add this
]
```

### 3. Backend: Register in Mind Service

**File**: `backend/src/services/mind_service.py`

Add to `MIND_TYPE_MAP` (around line 55):

```python
MIND_TYPE_MAP = {
    "project": Project,
    "task": Task,
    # ... existing mappings
    "sprint": Sprint,  # Add this - lowercase with underscores
}
```

**Important**: The key must be lowercase with underscores (e.g., `"sprint"`, `"acceptance_criteria"`).

### 3.5. Backend: Generate API Schemas (When Needed)

**When to run**: Only if you're adding a **brand new** Mind type or **modifying attributes** of an existing type.

**Command**:
```bash
cd backend
uv run python scripts/generate_schemas.py
```

**What it does**:
- Regenerates Pydantic schemas in `backend/src/schemas/` for API validation
- Updates OpenAPI documentation
- Ensures API endpoints validate the new/modified attributes correctly

**Skip this step if**: You're only adding frontend components for an existing backend Mind type (like we did with Sprint).

### 4. Frontend: Run Type Generation Script

**Command**:
```bash
cd frontends/web
npm run generate-types
# or
node scripts/generate-types.js
```

This generates:
- TypeScript interface in `src/types/generated.ts`
- Updates the `Mind` union type
- Updates the `NodeType` union type

### 5. Frontend: Create Node Component

**File**: `frontends/web/src/components/graph-editor/nodes/SprintNode.tsx`

```typescript
import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import type { Sprint } from '../../../types/generated';
import './BaseNode.css';

interface SprintNodeData {
  label: string;
  type: string;
  mind: Sprint;
  isFocused?: boolean;
  onMouseEnter?: (event: React.MouseEvent, nodeId: string) => void;
  onMouseLeave?: () => void;
}

export const SprintNode = memo(({ data, selected }: NodeProps<SprintNodeData>) => {
  const { label, mind, isFocused, onMouseEnter, onMouseLeave } = data;

  return (
    <div
      className={`base-node ${selected ? 'selected' : ''} ${isFocused ? 'focused' : ''}`}
      style={{ backgroundColor: '#f97316' }} // Choose a color
      onMouseEnter={(e) => onMouseEnter?.(e, mind.uuid!)}
      onMouseLeave={onMouseLeave}
    >
      <Handle type="target" position={Position.Top} />
      <div className="node-content">
        <div className="node-label">{label}</div>
        <div className="node-type">Sprint</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
});

SprintNode.displayName = 'SprintNode';
```

### 6. Frontend: Register Node Component

**File**: `frontends/web/src/components/graph-editor/nodes/index.tsx`

Add import and registration:

```typescript
import { SprintNode } from './SprintNode';

export const nodeTypes: NodeTypes = {
  // ... existing types
  Sprint: SprintNode,  // Add this
};

export const nodeColors: Record<string, string> = {
  // ... existing colors
  Sprint: '#f97316',  // Add this - choose a unique color
};

// Export the component
export {
  // ... existing exports
  SprintNode,
};
```

### 7. Frontend: Add Node Type Configuration

**File**: `frontends/web/src/components/graph-editor/nodeTypeConfig.ts`

Add configuration for the attribute editor:

```typescript
export const NODE_TYPE_CONFIGS: Record<NodeType, NodeTypeConfig> = {
  // ... existing configs
  Sprint: {
    displayName: 'Sprint',
    color: '#f97316',
    icon: '🏃',
    attributes: [
      {
        key: 'sprint_number',
        label: 'Sprint Number',
        type: 'number',
        required: true,
        editable: true,
      },
      {
        key: 'start_date',
        label: 'Start Date',
        type: 'date',
        required: true,
        editable: true,
      },
      {
        key: 'end_date',
        label: 'End Date',
        type: 'date',
        required: true,
        editable: true,
      },
      {
        key: 'goal',
        label: 'Sprint Goal',
        type: 'text',
        required: false,
        editable: true,
      },
      {
        key: 'velocity',
        label: 'Velocity',
        type: 'number',
        required: false,
        editable: true,
      },
    ],
  },
};
```

### 8. Frontend: Add to Create Node Form

**File**: `frontends/web/src/components/graph-editor/CreateNodeForm.tsx`

The form should automatically pick up the new type from the `NodeType` union, but verify it appears in the dropdown.

### 9. Test the New Mind Type

Create a test node via API or UI:

```bash
curl -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "sprint",
    "title": "Sprint 1",
    "creator": "test@example.com",
    "description": "First sprint",
    "status": "active",
    "type_specific_attributes": {
      "sprint_number": 1,
      "start_date": "2026-01-01",
      "end_date": "2026-01-14"
    }
  }'
```

## Checklist

Use this checklist when adding a new mind type:

- [ ] 1. Add class to `backend/src/models/mind_types.py`
- [ ] 2. Import and export in `backend/src/models/__init__.py`
- [ ] 3. Register in `backend/src/services/mind_service.py` MIND_TYPE_MAP
- [ ] 3.5. Run `uv run python scripts/generate_schemas.py` in backend (if new type or modified attributes)
- [ ] 4. Run `npm run generate-types` in frontend
- [ ] 5. Create node component in `frontends/web/src/components/graph-editor/nodes/`
- [ ] 6. Register in `frontends/web/src/components/graph-editor/nodes/index.tsx`
- [ ] 7. Add config in `frontends/web/src/components/graph-editor/nodeTypeConfig.ts`
- [ ] 8. Test creating a node via API
- [ ] 9. Test creating a node via UI
- [ ] 10. Test editing attributes
- [ ] 11. Test filtering by type
- [ ] 12. Update seed scripts if needed
- [ ] 13. Update `TODOHK/List.md` to mark item as done or in progress

## Common Issues

### Issue: Node doesn't appear in Create Node dropdown
**Solution**: Check that the type is in the generated `NodeType` union in `src/types/generated.ts`

### Issue: Node renders as blank or causes error
**Solution**: 
1. Check that node component is registered in `nodes/index.tsx`
2. Verify the mind_type conversion in `mindTypeToNodeType()` utility
3. Check browser console for errors

### Issue: Attributes don't show in editor
**Solution**: Add configuration in `nodeTypeConfig.ts`

### Issue: Backend returns 400 validation error
**Solution**: 
1. Check required fields are provided
2. Verify enum values are correct (uppercase for most, lowercase for severity/probability)
3. Check field types match the model definition

## Automation Opportunities

The following could be automated with a script:

1. Generate node component from template
2. Auto-register in nodes/index.tsx
3. Generate basic nodeTypeConfig entry
4. Update seed scripts

Consider creating a `scripts/add-mind-type.sh` script that takes a mind type name and generates all the boilerplate.
