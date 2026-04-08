/**
 * Unit tests for GraphEditorContext
 * Tests state management, reducer logic, and filtering functions
 */

import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import {
  GraphEditorProvider,
  useGraphEditor,
  type Mind,
  type Relationship,
} from './GraphEditorContext';

// Test wrapper component
function wrapper({ children }: { children: ReactNode }) {
  return <GraphEditorProvider>{children}</GraphEditorProvider>;
}

// Mock data
const mockMind1: Mind = {
  __primarylabel__: 'Project',
  uuid: 'uuid-1',
  title: 'Test Project',
  version: 1,
  creator: 'test-user',
  start_date: '2024-01-01',
  end_date: '2024-12-31',
};

const mockMind2: Mind = {
  __primarylabel__: 'Task',
  uuid: 'uuid-2',
  title: 'Test Task',
  version: 1,
  creator: 'test-user',
  priority: 'high',
};

const mockMind1v2: Mind = {
  ...mockMind1,
  version: 2,
  title: 'Test Project Updated',
};

const mockRelationship: Relationship = {
  id: 'rel-1',
  type: 'DEPENDS_ON',
  source: 'uuid-1',
  target: 'uuid-2',
};

describe('GraphEditorContext', () => {
  describe('useGraphEditor hook', () => {
    it('should throw error when used outside provider', () => {
      expect(() => {
        renderHook(() => useGraphEditor());
      }).toThrow('useGraphEditor must be used within a GraphEditorProvider');
    });

    it('should provide state and dispatch when used inside provider', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      expect(result.current.state).toBeDefined();
      expect(result.current.dispatch).toBeDefined();
      expect(result.current.state.minds).toBeInstanceOf(Map);
      expect(result.current.state.relationships).toBeInstanceOf(Map);
    });
  });

  describe('Initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      expect(result.current.state.minds.size).toBe(0);
      expect(result.current.state.relationships.size).toBe(0);
      expect(result.current.state.filters.nodeTypes.size).toBe(0);
      expect(result.current.state.filters.textSearch).toBe('');
      expect(result.current.state.filters.level).toBe(0);
      expect(result.current.state.filters.focusedNodeId).toBeNull();
      expect(result.current.state.selection.selectedNodeId).toBeNull();
      expect(result.current.state.selection.selectedEdgeId).toBeNull();
      expect(result.current.state.layout.algorithm).toBe('force-directed');
      expect(result.current.state.layout.distance).toBe(1.0);
      expect(result.current.state.loading).toBe(false);
      expect(result.current.state.error).toBeNull();
    });
  });

  describe('SET_MINDS action', () => {
    it('should set minds and update visible nodes', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
      });

      expect(result.current.state.minds.size).toBe(2);
      expect(result.current.state.minds.get('uuid-1')).toEqual(mockMind1);
      expect(result.current.state.minds.get('uuid-2')).toEqual(mockMind2);
      expect(result.current.state.visibleNodes).toContain('uuid-1');
      expect(result.current.state.visibleNodes).toContain('uuid-2');
    });

    it('should filter to current version only when multiple versions exist', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind1v2, mockMind2],
        });
      });

      expect(result.current.state.minds.size).toBe(2);
      expect(result.current.state.minds.get('uuid-1')).toEqual(mockMind1v2);
      expect(result.current.state.minds.get('uuid-1')?.version).toBe(2);
    });
  });

  describe('SET_RELATIONSHIPS action', () => {
    it('should set relationships and update visible edges', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [mockRelationship],
        });
      });

      expect(result.current.state.relationships.size).toBe(1);
      expect(result.current.state.relationships.get('rel-1')).toEqual(mockRelationship);
      expect(result.current.state.visibleEdges).toContain('rel-1');
    });
  });

  describe('ADD_MIND action', () => {
    it('should add a new mind', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'ADD_MIND',
          payload: mockMind1,
        });
      });

      expect(result.current.state.minds.size).toBe(1);
      expect(result.current.state.minds.get('uuid-1')).toEqual(mockMind1);
      expect(result.current.state.visibleNodes).toContain('uuid-1');
    });
  });

  describe('UPDATE_MIND action', () => {
    it('should update an existing mind', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1],
        });
        result.current.dispatch({
          type: 'UPDATE_MIND',
          payload: mockMind1v2,
        });
      });

      expect(result.current.state.minds.get('uuid-1')).toEqual(mockMind1v2);
      expect(result.current.state.minds.get('uuid-1')?.title).toBe('Test Project Updated');
    });
  });

  describe('DELETE_MIND action', () => {
    it('should delete a mind and its connected relationships', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [mockRelationship],
        });
        result.current.dispatch({
          type: 'DELETE_MIND',
          payload: 'uuid-1',
        });
      });

      expect(result.current.state.minds.size).toBe(1);
      expect(result.current.state.minds.has('uuid-1')).toBe(false);
      expect(result.current.state.relationships.size).toBe(0);
      expect(result.current.state.visibleEdges).not.toContain('rel-1');
    });

    it('should clear selection if deleted node was selected', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1],
        });
        result.current.dispatch({
          type: 'SELECT_NODE',
          payload: 'uuid-1',
        });
        result.current.dispatch({
          type: 'DELETE_MIND',
          payload: 'uuid-1',
        });
      });

      expect(result.current.state.selection.selectedNodeId).toBeNull();
    });
  });

  describe('Node type filtering', () => {
    it('should filter nodes by type', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_NODE_TYPE_FILTER',
          payload: new Set(['Project']),
        });
      });

      expect(result.current.state.visibleNodes).toContain('uuid-1');
      expect(result.current.state.visibleNodes).not.toContain('uuid-2');
    });

    it('should show all nodes when no types selected', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_NODE_TYPE_FILTER',
          payload: new Set(),
        });
      });

      expect(result.current.state.visibleNodes).toContain('uuid-1');
      expect(result.current.state.visibleNodes).toContain('uuid-2');
    });
  });

  describe('Text search filtering', () => {
    it('should filter nodes by text search', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_TEXT_SEARCH',
          payload: 'Project',
        });
      });

      expect(result.current.state.visibleNodes).toContain('uuid-1');
      expect(result.current.state.visibleNodes).not.toContain('uuid-2');
    });

    it('should be case-insensitive', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_TEXT_SEARCH',
          payload: 'project',
        });
      });

      expect(result.current.state.visibleNodes).toContain('uuid-1');
    });

    it('should include connected nodes when level > 0', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [mockRelationship],
        });
        result.current.dispatch({
          type: 'SET_TEXT_SEARCH',
          payload: 'Project',
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 1,
        });
      });

      expect(result.current.state.visibleNodes).toContain('uuid-1');
      expect(result.current.state.visibleNodes).toContain('uuid-2');
    });
  });

  describe('Selection', () => {
    it('should select a node', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SELECT_NODE',
          payload: 'uuid-1',
        });
      });

      expect(result.current.state.selection.selectedNodeId).toBe('uuid-1');
      expect(result.current.state.selection.selectedEdgeId).toBeNull();
    });

    it('should select an edge and clear node selection', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SELECT_NODE',
          payload: 'uuid-1',
        });
        result.current.dispatch({
          type: 'SELECT_EDGE',
          payload: 'rel-1',
        });
      });

      expect(result.current.state.selection.selectedNodeId).toBeNull();
      expect(result.current.state.selection.selectedEdgeId).toBe('rel-1');
    });
  });

  describe('Layout configuration', () => {
    it('should update layout algorithm', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_LAYOUT_ALGORITHM',
          payload: 'hierarchical',
        });
      });

      expect(result.current.state.layout.algorithm).toBe('hierarchical');
    });

    it('should update layout distance', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_LAYOUT_DISTANCE',
          payload: 1.5,
        });
      });

      expect(result.current.state.layout.distance).toBe(1.5);
    });
  });

  describe('RESET_FILTERS action', () => {
    it('should reset all filters to defaults', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_NODE_TYPE_FILTER',
          payload: new Set(['Project']),
        });
        result.current.dispatch({
          type: 'SET_TEXT_SEARCH',
          payload: 'test',
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 2,
        });
        result.current.dispatch({
          type: 'RESET_FILTERS',
        });
      });

      expect(result.current.state.filters.nodeTypes.size).toBe(0);
      expect(result.current.state.filters.textSearch).toBe('');
      expect(result.current.state.filters.level).toBe(0);
      expect(result.current.state.filters.focusedNodeId).toBeNull();
      expect(result.current.state.visibleNodes).toContain('uuid-1');
      expect(result.current.state.visibleNodes).toContain('uuid-2');
    });
  });

  describe('Loading and error states', () => {
    it('should set loading state', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_LOADING',
          payload: true,
        });
      });

      expect(result.current.state.loading).toBe(true);
    });

    it('should set error state', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_ERROR',
          payload: 'Test error message',
        });
      });

      expect(result.current.state.error).toBe('Test error message');
    });
  });

  describe('Edge filtering with node filters', () => {
    it('should hide edges when endpoints are filtered out', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [mockMind1, mockMind2],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [mockRelationship],
        });
        result.current.dispatch({
          type: 'SET_NODE_TYPE_FILTER',
          payload: new Set(['Project']),
        });
      });

      expect(result.current.state.visibleEdges).not.toContain('rel-1');
    });
  });

  describe('Undo/Redo functionality', () => {
    describe('History tracking', () => {
      it('should track mind creation in history', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
        });

        expect(result.current.state.history.past.length).toBe(1);
        expect(result.current.state.history.past[0]).toEqual({
          type: 'create',
          entityType: 'mind',
          entityId: 'uuid-1',
          previousData: null,
        });
        expect(result.current.state.canUndo).toBe(true);
        expect(result.current.state.canRedo).toBe(false);
      });

      it('should track mind update in history', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1],
          });
          result.current.dispatch({
            type: 'UPDATE_MIND',
            payload: mockMind1v2,
          });
        });

        expect(result.current.state.history.past.length).toBe(1);
        expect(result.current.state.history.past[0]).toEqual({
          type: 'update',
          entityType: 'mind',
          entityId: 'uuid-1',
          previousData: mockMind1,
        });
        expect(result.current.state.canUndo).toBe(true);
      });

      it('should track mind deletion in history', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1],
          });
          result.current.dispatch({
            type: 'DELETE_MIND',
            payload: 'uuid-1',
          });
        });

        expect(result.current.state.history.past.length).toBe(1);
        expect(result.current.state.history.past[0]).toEqual({
          type: 'delete',
          entityType: 'mind',
          entityId: 'uuid-1',
          previousData: mockMind1,
        });
        expect(result.current.state.canUndo).toBe(true);
      });

      it('should track relationship creation in history', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1, mockMind2],
          });
          result.current.dispatch({
            type: 'ADD_RELATIONSHIP',
            payload: mockRelationship,
          });
        });

        expect(result.current.state.history.past.length).toBe(1);
        expect(result.current.state.history.past[0]).toEqual({
          type: 'create',
          entityType: 'relationship',
          entityId: 'rel-1',
          previousData: null,
        });
        expect(result.current.state.canUndo).toBe(true);
      });

      it('should track relationship update in history', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        const updatedRelationship = { ...mockRelationship, type: 'RELATED_TO' };

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1, mockMind2],
          });
          result.current.dispatch({
            type: 'SET_RELATIONSHIPS',
            payload: [mockRelationship],
          });
          result.current.dispatch({
            type: 'UPDATE_RELATIONSHIP',
            payload: updatedRelationship,
          });
        });

        expect(result.current.state.history.past.length).toBe(1);
        expect(result.current.state.history.past[0]).toEqual({
          type: 'update',
          entityType: 'relationship',
          entityId: 'rel-1',
          previousData: mockRelationship,
        });
        expect(result.current.state.canUndo).toBe(true);
      });

      it('should track relationship deletion in history', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1, mockMind2],
          });
          result.current.dispatch({
            type: 'SET_RELATIONSHIPS',
            payload: [mockRelationship],
          });
          result.current.dispatch({
            type: 'DELETE_RELATIONSHIP',
            payload: 'rel-1',
          });
        });

        expect(result.current.state.history.past.length).toBe(1);
        expect(result.current.state.history.past[0]).toEqual({
          type: 'delete',
          entityType: 'relationship',
          entityId: 'rel-1',
          previousData: mockRelationship,
        });
        expect(result.current.state.canUndo).toBe(true);
      });

      it('should clear future stack when new action is performed', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.history.future.length).toBe(1);
        expect(result.current.state.canRedo).toBe(true);

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind2,
          });
        });

        expect(result.current.state.history.future.length).toBe(0);
        expect(result.current.state.canRedo).toBe(false);
      });

      it('should limit history stack to 50 operations', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          // Add 51 minds to exceed the limit
          for (let i = 0; i < 51; i++) {
            result.current.dispatch({
              type: 'ADD_MIND',
              payload: {
                __primarylabel__: 'Task',
                uuid: `uuid-${i}`,
                title: `Task ${i}`,
                version: 1,
                creator: 'test-user',
                priority: 'medium',
              },
            });
          }
        });

        expect(result.current.state.history.past.length).toBe(50);
        expect(result.current.state.history.past[0].entityId).toBe('uuid-1'); // First action removed
        expect(result.current.state.canUndo).toBe(true);
      });
    });

    describe('Undo operations', () => {
      it('should undo mind creation', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(true);

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(false);
        expect(result.current.state.history.past.length).toBe(0);
        expect(result.current.state.history.future.length).toBe(1);
        expect(result.current.state.canUndo).toBe(false);
        expect(result.current.state.canRedo).toBe(true);
      });

      it('should undo mind update', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1],
          });
          result.current.dispatch({
            type: 'UPDATE_MIND',
            payload: mockMind1v2,
          });
        });

        expect(result.current.state.minds.get('uuid-1')?.title).toBe('Test Project Updated');

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.get('uuid-1')?.title).toBe('Test Project');
        expect(result.current.state.minds.get('uuid-1')?.version).toBe(1);
        expect(result.current.state.canRedo).toBe(true);
      });

      it('should undo mind deletion', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1],
          });
          result.current.dispatch({
            type: 'DELETE_MIND',
            payload: 'uuid-1',
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(false);

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(true);
        expect(result.current.state.minds.get('uuid-1')).toEqual(mockMind1);
        expect(result.current.state.canRedo).toBe(true);
      });

      it('should undo relationship creation', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1, mockMind2],
          });
          result.current.dispatch({
            type: 'ADD_RELATIONSHIP',
            payload: mockRelationship,
          });
        });

        expect(result.current.state.relationships.has('rel-1')).toBe(true);

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.relationships.has('rel-1')).toBe(false);
        expect(result.current.state.canRedo).toBe(true);
      });

      it('should undo relationship update', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        const updatedRelationship = { ...mockRelationship, type: 'RELATED_TO' };

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1, mockMind2],
          });
          result.current.dispatch({
            type: 'SET_RELATIONSHIPS',
            payload: [mockRelationship],
          });
          result.current.dispatch({
            type: 'UPDATE_RELATIONSHIP',
            payload: updatedRelationship,
          });
        });

        expect(result.current.state.relationships.get('rel-1')?.type).toBe('RELATED_TO');

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.relationships.get('rel-1')?.type).toBe('DEPENDS_ON');
        expect(result.current.state.canRedo).toBe(true);
      });

      it('should undo relationship deletion', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1, mockMind2],
          });
          result.current.dispatch({
            type: 'SET_RELATIONSHIPS',
            payload: [mockRelationship],
          });
          result.current.dispatch({
            type: 'DELETE_RELATIONSHIP',
            payload: 'rel-1',
          });
        });

        expect(result.current.state.relationships.has('rel-1')).toBe(false);

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.relationships.has('rel-1')).toBe(true);
        expect(result.current.state.relationships.get('rel-1')).toEqual(mockRelationship);
        expect(result.current.state.canRedo).toBe(true);
      });

      it('should handle multiple undo operations', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind2,
          });
        });

        expect(result.current.state.minds.size).toBe(2);

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.size).toBe(1);
        expect(result.current.state.minds.has('uuid-1')).toBe(true);

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.size).toBe(0);
        expect(result.current.state.canUndo).toBe(false);
      });

      it('should do nothing when undo is called with empty history', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        const stateBefore = result.current.state;

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state).toEqual(stateBefore);
        expect(result.current.state.canUndo).toBe(false);
      });
    });

    describe('Redo operations', () => {
      it('should redo mind creation', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(false);

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(true);
        expect(result.current.state.minds.get('uuid-1')).toEqual(mockMind1);
        expect(result.current.state.canRedo).toBe(false);
        expect(result.current.state.canUndo).toBe(true);
      });

      it('should redo mind update', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1],
          });
          result.current.dispatch({
            type: 'UPDATE_MIND',
            payload: mockMind1v2,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.get('uuid-1')?.title).toBe('Test Project');

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.minds.get('uuid-1')?.title).toBe('Test Project Updated');
        expect(result.current.state.canRedo).toBe(false);
      });

      it('should redo mind deletion', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1],
          });
          result.current.dispatch({
            type: 'DELETE_MIND',
            payload: 'uuid-1',
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(true);

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.minds.has('uuid-1')).toBe(false);
        expect(result.current.state.canRedo).toBe(false);
      });

      it('should redo relationship creation', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'SET_MINDS',
            payload: [mockMind1, mockMind2],
          });
          result.current.dispatch({
            type: 'ADD_RELATIONSHIP',
            payload: mockRelationship,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.relationships.has('rel-1')).toBe(false);

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.relationships.has('rel-1')).toBe(true);
        expect(result.current.state.relationships.get('rel-1')).toEqual(mockRelationship);
        expect(result.current.state.canRedo).toBe(false);
      });

      it('should handle multiple redo operations', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind2,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.minds.size).toBe(0);

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.minds.size).toBe(1);
        expect(result.current.state.minds.has('uuid-1')).toBe(true);

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.minds.size).toBe(2);
        expect(result.current.state.minds.has('uuid-2')).toBe(true);
        expect(result.current.state.canRedo).toBe(false);
      });

      it('should do nothing when redo is called with empty future stack', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
        });

        const stateBefore = result.current.state;

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state).toEqual(stateBefore);
        expect(result.current.state.canRedo).toBe(false);
      });
    });

    describe('Undo/Redo consistency', () => {
      it('should return to original state after undo followed by redo', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
        });

        const stateAfterAdd = result.current.state;

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.minds).toEqual(stateAfterAdd.minds);
        expect(result.current.state.relationships).toEqual(stateAfterAdd.relationships);
      });

      it('should maintain state consistency through multiple undo/redo cycles', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind2,
          });
        });

        const finalState = result.current.state;

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
          result.current.dispatch({
            type: 'UNDO',
          });
          result.current.dispatch({
            type: 'REDO',
          });
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.minds).toEqual(finalState.minds);
        expect(result.current.state.relationships).toEqual(finalState.relationships);
      });

      it('should update visible nodes after undo/redo', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
        });

        expect(result.current.state.visibleNodes).toContain('uuid-1');

        act(() => {
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.visibleNodes).not.toContain('uuid-1');

        act(() => {
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.visibleNodes).toContain('uuid-1');
      });
    });

    describe('canUndo and canRedo flags', () => {
      it('should set canUndo to true when history has actions', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        expect(result.current.state.canUndo).toBe(false);

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
        });

        expect(result.current.state.canUndo).toBe(true);
      });

      it('should set canUndo to false when history is empty', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.canUndo).toBe(false);
      });

      it('should set canRedo to true when future stack has actions', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        expect(result.current.state.canRedo).toBe(false);

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
        });

        expect(result.current.state.canRedo).toBe(true);
      });

      it('should set canRedo to false when future stack is empty', () => {
        const { result } = renderHook(() => useGraphEditor(), { wrapper });

        act(() => {
          result.current.dispatch({
            type: 'ADD_MIND',
            payload: mockMind1,
          });
          result.current.dispatch({
            type: 'UNDO',
          });
          result.current.dispatch({
            type: 'REDO',
          });
        });

        expect(result.current.state.canRedo).toBe(false);
      });
    });
  });

  describe('Focus mode filtering', () => {
    // Create a more complex graph for focus mode testing
    const node1: Mind = {
      __primarylabel__: 'Project',
      uuid: 'node-1',
      title: 'Node 1',
      version: 1,
      creator: 'test-user',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
    };

    const node2: Mind = {
      __primarylabel__: 'Task',
      uuid: 'node-2',
      title: 'Node 2',
      version: 1,
      creator: 'test-user',
      priority: 'high',
    };

    const node3: Mind = {
      __primarylabel__: 'Task',
      uuid: 'node-3',
      title: 'Node 3',
      version: 1,
      creator: 'test-user',
      priority: 'medium',
    };

    const node4: Mind = {
      __primarylabel__: 'Task',
      uuid: 'node-4',
      title: 'Node 4',
      version: 1,
      creator: 'test-user',
      priority: 'low',
    };

    const edge1to2: Relationship = {
      id: 'edge-1-2',
      type: 'DEPENDS_ON',
      source: 'node-1',
      target: 'node-2',
    };

    const edge2to3: Relationship = {
      id: 'edge-2-3',
      type: 'DEPENDS_ON',
      source: 'node-2',
      target: 'node-3',
    };

    const edge3to4: Relationship = {
      id: 'edge-3-4',
      type: 'DEPENDS_ON',
      source: 'node-3',
      target: 'node-4',
    };

    it('should activate focus mode when SET_FOCUS_MODE is dispatched', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
      });

      expect(result.current.state.filters.focusedNodeId).toBe('node-1');
    });

    it('should show only focused node when level is 0', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [edge1to2, edge2to3, edge3to4],
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 0,
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
      });

      expect(result.current.state.visibleNodes).toEqual(['node-1']);
      expect(result.current.state.visibleEdges).toEqual([]);
    });

    it('should show focused node and nodes within 1 hop when level is 1', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [edge1to2, edge2to3, edge3to4],
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 1,
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
      });

      expect(result.current.state.visibleNodes).toContain('node-1');
      expect(result.current.state.visibleNodes).toContain('node-2');
      expect(result.current.state.visibleNodes).not.toContain('node-3');
      expect(result.current.state.visibleNodes).not.toContain('node-4');
      expect(result.current.state.visibleEdges).toContain('edge-1-2');
      expect(result.current.state.visibleEdges).not.toContain('edge-2-3');
    });

    it('should show focused node and nodes within 2 hops when level is 2', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [edge1to2, edge2to3, edge3to4],
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 2,
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
      });

      expect(result.current.state.visibleNodes).toContain('node-1');
      expect(result.current.state.visibleNodes).toContain('node-2');
      expect(result.current.state.visibleNodes).toContain('node-3');
      expect(result.current.state.visibleNodes).not.toContain('node-4');
      expect(result.current.state.visibleEdges).toContain('edge-1-2');
      expect(result.current.state.visibleEdges).toContain('edge-2-3');
      expect(result.current.state.visibleEdges).not.toContain('edge-3-4');
    });

    it('should update visible nodes when level changes in focus mode', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [edge1to2, edge2to3, edge3to4],
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 0,
        });
      });

      expect(result.current.state.visibleNodes).toEqual(['node-1']);

      act(() => {
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 1,
        });
      });

      expect(result.current.state.visibleNodes).toContain('node-1');
      expect(result.current.state.visibleNodes).toContain('node-2');
    });

    it('should remove edges with filtered endpoints in focus mode', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [edge1to2, edge2to3, edge3to4],
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 1,
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
      });

      // Only edge-1-2 should be visible (connects node-1 and node-2)
      // edge-2-3 should not be visible because node-3 is not in the visible set
      expect(result.current.state.visibleEdges).toContain('edge-1-2');
      expect(result.current.state.visibleEdges).not.toContain('edge-2-3');
      expect(result.current.state.visibleEdges).not.toContain('edge-3-4');
    });

    it('should exit focus mode when focusedNodeId is set to null', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
      });

      expect(result.current.state.filters.focusedNodeId).toBe('node-1');

      act(() => {
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: null,
        });
      });

      expect(result.current.state.filters.focusedNodeId).toBeNull();
      expect(result.current.state.visibleNodes).toContain('node-1');
      expect(result.current.state.visibleNodes).toContain('node-2');
      expect(result.current.state.visibleNodes).toContain('node-3');
      expect(result.current.state.visibleNodes).toContain('node-4');
    });

    it('should work with node type filters in focus mode', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_RELATIONSHIPS',
          payload: [edge1to2, edge2to3, edge3to4],
        });
        result.current.dispatch({
          type: 'SET_NODE_TYPE_FILTER',
          payload: new Set(['Task']),
        });
        result.current.dispatch({
          type: 'SET_LEVEL',
          payload: 1,
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-2',
        });
      });

      // node-1 is filtered out by type filter (it's a Project)
      // node-2 is the focused node (Task)
      // node-3 is within 1 hop and is a Task
      expect(result.current.state.visibleNodes).not.toContain('node-1');
      expect(result.current.state.visibleNodes).toContain('node-2');
      expect(result.current.state.visibleNodes).toContain('node-3');
      expect(result.current.state.visibleNodes).not.toContain('node-4');
    });

    it('should reset focus mode when RESET_FILTERS is dispatched', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({
          type: 'SET_MINDS',
          payload: [node1, node2, node3, node4],
        });
        result.current.dispatch({
          type: 'SET_FOCUS_MODE',
          payload: 'node-1',
        });
        result.current.dispatch({
          type: 'RESET_FILTERS',
        });
      });

      expect(result.current.state.filters.focusedNodeId).toBeNull();
      expect(result.current.state.visibleNodes.length).toBe(4);
    });
  });

  describe('Relationship type filtering', () => {
    const mindA: Mind = {
      __primarylabel__: 'Project',
      uuid: 'a',
      title: 'A',
      version: 1,
      creator: 'user',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
    };
    const mindB: Mind = {
      __primarylabel__: 'Task',
      uuid: 'b',
      title: 'B',
      version: 1,
      creator: 'user',
      priority: 'medium',
    };
    const mindC: Mind = {
      __primarylabel__: 'Task',
      uuid: 'c',
      title: 'C',
      version: 1,
      creator: 'user',
      priority: 'high',
    };
    const relAB: Relationship = { id: 'r1', type: 'DEPENDS_ON', source: 'a', target: 'b' };
    const relBC: Relationship = { id: 'r2', type: 'CONTAINS', source: 'b', target: 'c' };
    const relAC: Relationship = { id: 'r3', type: 'DEPENDS_ON', source: 'a', target: 'c' };

    it('should show all edges when relationship type filter is empty', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({ type: 'SET_MINDS', payload: [mindA, mindB, mindC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIPS', payload: [relAB, relBC, relAC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: new Set() });
      });

      expect(result.current.state.visibleEdges).toContain('r1');
      expect(result.current.state.visibleEdges).toContain('r2');
      expect(result.current.state.visibleEdges).toContain('r3');
    });

    it('should show only edges matching selected relationship types', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({ type: 'SET_MINDS', payload: [mindA, mindB, mindC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIPS', payload: [relAB, relBC, relAC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: new Set(['DEPENDS_ON']) });
      });

      expect(result.current.state.visibleEdges).toContain('r1');
      expect(result.current.state.visibleEdges).not.toContain('r2');
      expect(result.current.state.visibleEdges).toContain('r3');
    });

    it('should show only CONTAINS edges when filtered', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({ type: 'SET_MINDS', payload: [mindA, mindB, mindC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIPS', payload: [relAB, relBC, relAC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: new Set(['CONTAINS']) });
      });

      expect(result.current.state.visibleEdges).not.toContain('r1');
      expect(result.current.state.visibleEdges).toContain('r2');
      expect(result.current.state.visibleEdges).not.toContain('r3');
    });

    it('should compose with existing node type filters', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({ type: 'SET_MINDS', payload: [mindA, mindB, mindC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIPS', payload: [relAB, relBC, relAC] });
        // Even with relationship type filter, edges with filtered-out endpoints are hidden
        result.current.dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: new Set(['DEPENDS_ON']) });
      });

      // Both DEPENDS_ON edges should be visible (r1: a->b, r3: a->c)
      expect(result.current.state.visibleEdges).toContain('r1');
      expect(result.current.state.visibleEdges).toContain('r3');
      expect(result.current.state.visibleEdges).not.toContain('r2');
    });
  });

  describe('Direction filtering', () => {
    const mindA: Mind = {
      __primarylabel__: 'Project',
      uuid: 'a',
      title: 'A',
      version: 1,
      creator: 'user',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
    };
    const mindB: Mind = {
      __primarylabel__: 'Task',
      uuid: 'b',
      title: 'B',
      version: 1,
      creator: 'user',
      priority: 'medium',
    };
    const mindC: Mind = {
      __primarylabel__: 'Task',
      uuid: 'c',
      title: 'C',
      version: 1,
      creator: 'user',
      priority: 'high',
    };
    // a -> b (outgoing from a)
    const relAB: Relationship = { id: 'r1', type: 'DEPENDS_ON', source: 'a', target: 'b' };
    // c -> a (incoming to a)
    const relCA: Relationship = { id: 'r2', type: 'CONTAINS', source: 'c', target: 'a' };
    // b -> c (neither outgoing from a nor incoming to a)
    const relBC: Relationship = { id: 'r3', type: 'DEPENDS_ON', source: 'b', target: 'c' };

    it('should show all edges when direction filter is null', () => {
      const wrapperWithFocus = ({ children }: { children: ReactNode }) => (
        <GraphEditorProvider
          initialMinds={[mindA, mindB, mindC]}
          initialRelationships={[relAB, relCA, relBC]}
          initialFocusedNodeId="a"
        >
          {children}
        </GraphEditorProvider>
      );
      const { result } = renderHook(() => useGraphEditor(), { wrapper: wrapperWithFocus });

      act(() => {
        result.current.dispatch({ type: 'SET_LEVEL', payload: 2 });
        result.current.dispatch({ type: 'SET_DIRECTION_FILTER', payload: null });
      });

      expect(result.current.state.visibleEdges).toContain('r1');
      expect(result.current.state.visibleEdges).toContain('r2');
      expect(result.current.state.visibleEdges).toContain('r3');
    });

    it('should show all edges when direction filter is both', () => {
      const wrapperWithFocus = ({ children }: { children: ReactNode }) => (
        <GraphEditorProvider
          initialMinds={[mindA, mindB, mindC]}
          initialRelationships={[relAB, relCA, relBC]}
          initialFocusedNodeId="a"
        >
          {children}
        </GraphEditorProvider>
      );
      const { result } = renderHook(() => useGraphEditor(), { wrapper: wrapperWithFocus });

      act(() => {
        result.current.dispatch({ type: 'SET_LEVEL', payload: 2 });
        result.current.dispatch({ type: 'SET_DIRECTION_FILTER', payload: 'both' });
      });

      expect(result.current.state.visibleEdges).toContain('r1');
      expect(result.current.state.visibleEdges).toContain('r2');
      expect(result.current.state.visibleEdges).toContain('r3');
    });

    it('should show only outgoing edges from focused node', () => {
      const wrapperWithFocus = ({ children }: { children: ReactNode }) => (
        <GraphEditorProvider
          initialMinds={[mindA, mindB, mindC]}
          initialRelationships={[relAB, relCA, relBC]}
          initialFocusedNodeId="a"
        >
          {children}
        </GraphEditorProvider>
      );
      const { result } = renderHook(() => useGraphEditor(), { wrapper: wrapperWithFocus });

      act(() => {
        result.current.dispatch({ type: 'SET_LEVEL', payload: 2 });
        result.current.dispatch({ type: 'SET_DIRECTION_FILTER', payload: 'outgoing' });
      });

      // r1: a->b (outgoing from a) ✓
      expect(result.current.state.visibleEdges).toContain('r1');
      // r2: c->a (incoming to a) ✗
      expect(result.current.state.visibleEdges).not.toContain('r2');
      // r3: b->c (not connected to a as source) ✗
      expect(result.current.state.visibleEdges).not.toContain('r3');
    });

    it('should show only incoming edges to focused node', () => {
      const wrapperWithFocus = ({ children }: { children: ReactNode }) => (
        <GraphEditorProvider
          initialMinds={[mindA, mindB, mindC]}
          initialRelationships={[relAB, relCA, relBC]}
          initialFocusedNodeId="a"
        >
          {children}
        </GraphEditorProvider>
      );
      const { result } = renderHook(() => useGraphEditor(), { wrapper: wrapperWithFocus });

      act(() => {
        result.current.dispatch({ type: 'SET_LEVEL', payload: 2 });
        result.current.dispatch({ type: 'SET_DIRECTION_FILTER', payload: 'incoming' });
      });

      // r1: a->b (outgoing from a) ✗
      expect(result.current.state.visibleEdges).not.toContain('r1');
      // r2: c->a (incoming to a) ✓
      expect(result.current.state.visibleEdges).toContain('r2');
      // r3: b->c (not connected to a as target) ✗
      expect(result.current.state.visibleEdges).not.toContain('r3');
    });

    it('should not apply direction filter when no focused node', () => {
      const { result } = renderHook(() => useGraphEditor(), { wrapper });

      act(() => {
        result.current.dispatch({ type: 'SET_MINDS', payload: [mindA, mindB, mindC] });
        result.current.dispatch({ type: 'SET_RELATIONSHIPS', payload: [relAB, relCA, relBC] });
        result.current.dispatch({ type: 'SET_DIRECTION_FILTER', payload: 'outgoing' });
      });

      // No focused node, so direction filter should be a no-op
      expect(result.current.state.visibleEdges).toContain('r1');
      expect(result.current.state.visibleEdges).toContain('r2');
      expect(result.current.state.visibleEdges).toContain('r3');
    });

    it('should compose direction filter with relationship type filter', () => {
      const wrapperWithFocus = ({ children }: { children: ReactNode }) => (
        <GraphEditorProvider
          initialMinds={[mindA, mindB, mindC]}
          initialRelationships={[relAB, relCA, relBC]}
          initialFocusedNodeId="a"
        >
          {children}
        </GraphEditorProvider>
      );
      const { result } = renderHook(() => useGraphEditor(), { wrapper: wrapperWithFocus });

      act(() => {
        result.current.dispatch({ type: 'SET_LEVEL', payload: 2 });
        // Filter to DEPENDS_ON only + outgoing from a
        result.current.dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: new Set(['DEPENDS_ON']) });
        result.current.dispatch({ type: 'SET_DIRECTION_FILTER', payload: 'outgoing' });
      });

      // r1: a->b, DEPENDS_ON, outgoing from a ✓
      expect(result.current.state.visibleEdges).toContain('r1');
      // r2: c->a, CONTAINS (filtered out by type) ✗
      expect(result.current.state.visibleEdges).not.toContain('r2');
      // r3: b->c, DEPENDS_ON but not outgoing from a ✗
      expect(result.current.state.visibleEdges).not.toContain('r3');
    });
  });
});
