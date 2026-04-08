/**
 * GraphEditorContext - Centralized state management for the Mind Graph Editor
 * 
 * Uses React Context API with useReducer for state management
 * Manages raw data (minds, relationships), UI state (filters, selection, layout),
 * and derived state (visible nodes/edges)
 * 
 * **Validates: Requirements 1.1, 2.1, 3.1, 4.1**
 */

import React, { createContext, useContext, useReducer, useMemo } from 'react';
import type { ReactNode } from 'react';
import type { Mind, NodeType } from '../../types/generated';
import type { RelationshipType } from '../../types';
import { mindTypeToNodeType } from '../../utils/mindTypeUtils';

// Re-export types for convenience
export type { Mind, NodeType } from '../../types/generated';
export type { RelationshipType } from '../../types';

// ============================================================================
// Types
// ============================================================================

/**
 * UUID type for Mind identifiers
 */
export type UUID = string;

/**
 * Layout algorithm options
 */
export type LayoutAlgorithm = 'force-directed' | 'hierarchical' | 'circular' | 'grid';

/**
 * Relationship interface
 */
export interface Relationship {
  id: string;
  type: string;
  source: UUID;
  target: UUID;
  properties?: Record<string, unknown>;
}

/**
 * Fast Add mode state for streamlined node + relationship creation
 */
export interface FastAddState {
  enabled: boolean;
  selectedMindType: NodeType | null;
  selectedRelationshipType: RelationshipType | null;
  relationDirection: 'source' | 'target';
}

/**
 * Pick mode state for click-to-select in relationship editor
 */
export interface PickModeState {
  active: boolean;
  field: 'source' | 'target';
}

/**
 * Filter state
 */
export interface FilterState {
  nodeTypes: Set<NodeType>;
  textSearch: string;
  level: number;
  focusedNodeId: UUID | null;
  relationshipTypes: Set<RelationshipType>;
  directionFilter: 'outgoing' | 'incoming' | 'both' | null;
}

/**
 * Selection state
 */
export interface SelectionState {
  selectedNodeId: UUID | null;
  selectedEdgeId: string | null;
}

/**
 * Layout configuration
 */
export interface LayoutConfig {
  algorithm: LayoutAlgorithm;
  distance: number;
}

/**
 * Action for undo/redo history
 * Stores the previous state before an operation for undo
 */
export interface HistoryAction {
  type: 'create' | 'update' | 'delete';
  entityType: 'mind' | 'relationship';
  entityId: string;
  previousData?: Mind | Relationship | null; // null for create (no previous state)
}

/**
 * History state for undo/redo
 */
export interface HistoryState {
  past: HistoryAction[];
  future: HistoryAction[];
  maxSize: number;
}

/**
 * Main application state
 */
export interface AppState {
  // Raw data from backend
  minds: Map<UUID, Mind>;
  relationships: Map<string, Relationship>;
  
  // UI state
  filters: FilterState;
  selection: SelectionState;
  layout: LayoutConfig;
  history: HistoryState;
  fastAdd: FastAddState;
  pickMode: PickModeState | null;
  filterPanelCollapsed: boolean;
  
  // Derived state (computed from raw data + filters)
  visibleNodes: UUID[];
  visibleEdges: string[];
  
  // Undo/redo flags
  canUndo: boolean;
  canRedo: boolean;
  
  // Loading/error state
  loading: boolean;
  error: string | null;
}

// ============================================================================
// Actions
// ============================================================================

export type Action =
  | { type: 'SET_MINDS'; payload: Mind[] }
  | { type: 'SET_RELATIONSHIPS'; payload: Relationship[] }
  | { type: 'ADD_MIND'; payload: Mind }
  | { type: 'UPDATE_MIND'; payload: Mind }
  | { type: 'DELETE_MIND'; payload: UUID }
  | { type: 'ADD_RELATIONSHIP'; payload: Relationship }
  | { type: 'UPDATE_RELATIONSHIP'; payload: Relationship }
  | { type: 'DELETE_RELATIONSHIP'; payload: string }
  | { type: 'SET_NODE_TYPE_FILTER'; payload: Set<NodeType> }
  | { type: 'SET_TEXT_SEARCH'; payload: string }
  | { type: 'SET_LEVEL'; payload: number }
  | { type: 'SET_FOCUS_MODE'; payload: UUID | null }
  | { type: 'RESET_FILTERS' }
  | { type: 'SELECT_NODE'; payload: UUID | null }
  | { type: 'SELECT_EDGE'; payload: string | null }
  | { type: 'SET_LAYOUT_ALGORITHM'; payload: LayoutAlgorithm }
  | { type: 'SET_LAYOUT_DISTANCE'; payload: number }
  | { type: 'UNDO' }
  | { type: 'REDO' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_FAST_ADD_ENABLED'; payload: boolean }
  | { type: 'SET_FAST_ADD_MIND_TYPE'; payload: NodeType | null }
  | { type: 'SET_FAST_ADD_RELATIONSHIP_TYPE'; payload: RelationshipType | null }
  | { type: 'SET_FAST_ADD_DIRECTION'; payload: 'source' | 'target' }
  | { type: 'SET_PICK_MODE'; payload: PickModeState | null }
  | { type: 'SET_FILTER_PANEL_COLLAPSED'; payload: boolean }
  | { type: 'SET_RELATIONSHIP_TYPE_FILTER'; payload: Set<RelationshipType> }
  | { type: 'SET_DIRECTION_FILTER'; payload: 'outgoing' | 'incoming' | 'both' | null };

// ============================================================================
// Initial State
// ============================================================================

const initialState: AppState = {
  minds: new Map(),
  relationships: new Map(),
  filters: {
    nodeTypes: new Set(),
    textSearch: '',
    level: 0,
    focusedNodeId: null,
    relationshipTypes: new Set(),
    directionFilter: null,
  },
  selection: {
    selectedNodeId: null,
    selectedEdgeId: null,
  },
  layout: {
    algorithm: 'hierarchical',
    distance: 1.0,
  },
  history: {
    past: [],
    future: [],
    maxSize: 50,
  },
  fastAdd: {
    enabled: false,
    selectedMindType: null,
    selectedRelationshipType: null,
    relationDirection: 'source',
  },
  pickMode: null,
  filterPanelCollapsed: false,
  visibleNodes: [],
  visibleEdges: [],
  canUndo: false,
  canRedo: false,
  loading: false,
  error: null,
};

// ============================================================================
// Filtering Logic
// ============================================================================

/**
 * Filter minds by node type
 */
function filterByNodeType(minds: Mind[], selectedTypes: Set<NodeType>): Mind[] {
  if (selectedTypes.size === 0) return minds;
  return minds.filter(m => {
    // Backend returns lowercase mind_type, capitalize it to match NodeType
    const nodeType = mindTypeToNodeType((m as any).mind_type) as NodeType;
    return selectedTypes.has(nodeType);
  });
}

/**
 * Filter by text search with proximity (BFS)
 */
function filterByTextSearch(
  minds: Mind[],
  relationships: Relationship[],
  searchText: string,
  level: number
): { nodes: Mind[], edges: Relationship[] } {
  if (!searchText) return { nodes: minds, edges: relationships };
  
  // Find direct matches
  const matches = minds.filter(m => 
    m.title.toLowerCase().includes(searchText.toLowerCase())
  );
  
  if (level === 0) {
    return { nodes: matches, edges: [] };
  }
  
  // BFS to find nodes within N hops
  const visible = new Set(matches.map(m => m.uuid!));
  const queue: Array<{ id: UUID, depth: number }> = 
    matches.map(m => ({ id: m.uuid!, depth: 0 }));
  
  while (queue.length > 0) {
    const { id, depth } = queue.shift()!;
    if (depth >= level) continue;
    
    // Find connected nodes
    const connected = relationships
      .filter(r => r.source === id || r.target === id)
      .flatMap(r => [r.source, r.target])
      .filter(nodeId => !visible.has(nodeId));
    
    connected.forEach(nodeId => {
      visible.add(nodeId);
      queue.push({ id: nodeId, depth: depth + 1 });
    });
  }
  
  const visibleNodes = minds.filter(m => visible.has(m.uuid!));
  const visibleEdges = relationships.filter(r => 
    visible.has(r.source) && visible.has(r.target)
  );
  
  return { nodes: visibleNodes, edges: visibleEdges };
}

/**
 * Filter by focus mode (BFS from focused node)
 */
function filterByFocus(
  minds: Mind[],
  relationships: Relationship[],
  focusedNodeId: UUID | null,
  level: number
): { nodes: Mind[], edges: Relationship[] } {
  if (!focusedNodeId) return { nodes: minds, edges: relationships };
  
  // Same BFS logic as text search, but starting from single node
  const visible = new Set([focusedNodeId]);
  const queue: Array<{ id: UUID, depth: number }> = [
    { id: focusedNodeId, depth: 0 }
  ];
  
  while (queue.length > 0) {
    const { id, depth } = queue.shift()!;
    if (depth >= level) continue;
    
    const connected = relationships
      .filter(r => r.source === id || r.target === id)
      .flatMap(r => [r.source, r.target])
      .filter(nodeId => !visible.has(nodeId));
    
    connected.forEach(nodeId => {
      visible.add(nodeId);
      queue.push({ id: nodeId, depth: depth + 1 });
    });
  }
  
  const visibleNodes = minds.filter(m => visible.has(m.uuid!));
  const visibleEdges = relationships.filter(r => 
    visible.has(r.source) && visible.has(r.target)
  );
  
  return { nodes: visibleNodes, edges: visibleEdges };
}

/**
 * Apply all filters in sequence
 */
function applyFilters(
  minds: Map<UUID, Mind>,
  relationships: Map<string, Relationship>,
  filters: FilterState
): { visibleNodes: UUID[], visibleEdges: string[] } {
  // Convert maps to arrays
  let nodeArray = Array.from(minds.values());
  let edgeArray = Array.from(relationships.values());
  
  // 1. Node type filter
  nodeArray = filterByNodeType(nodeArray, filters.nodeTypes);
  
  // 2. Focus mode (if active)
  if (filters.focusedNodeId) {
    const result = filterByFocus(nodeArray, edgeArray, filters.focusedNodeId, filters.level);
    nodeArray = result.nodes;
    edgeArray = result.edges;
  }
  
  // 3. Text search (if active)
  if (filters.textSearch) {
    const result = filterByTextSearch(nodeArray, edgeArray, filters.textSearch, filters.level);
    nodeArray = result.nodes;
    edgeArray = result.edges;
  }
  
  // 4. Remove edges with filtered endpoints
  const visibleNodeIds = new Set(nodeArray.map(n => n.uuid!));
  edgeArray = edgeArray.filter(e => 
    visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
  );
  
  // 5. Relationship type filter (Req 6.3, 6.5)
  if (filters.relationshipTypes.size > 0) {
    edgeArray = edgeArray.filter(e =>
      filters.relationshipTypes.has(e.type as RelationshipType)
    );
  }
  
  // 6. Direction filter relative to focused/selected node (Req 6.4)
  //    Uses BFS to follow edges in the specified direction across multiple hops.
  if (filters.directionFilter && filters.directionFilter !== 'both' && filters.focusedNodeId) {
    const refNodeId = filters.focusedNodeId;
    const reachable = new Set<UUID>([refNodeId]);
    const queue: UUID[] = [refNodeId];

    while (queue.length > 0) {
      const current = queue.shift()!;
      for (const e of edgeArray) {
        if (filters.directionFilter === 'incoming' && e.target === current && !reachable.has(e.source)) {
          reachable.add(e.source);
          queue.push(e.source);
        }
        if (filters.directionFilter === 'outgoing' && e.source === current && !reachable.has(e.target)) {
          reachable.add(e.target);
          queue.push(e.target);
        }
      }
    }

    edgeArray = edgeArray.filter(e => {
      if (filters.directionFilter === 'incoming') {
        return reachable.has(e.source) && reachable.has(e.target);
      }
      if (filters.directionFilter === 'outgoing') {
        return reachable.has(e.source) && reachable.has(e.target);
      }
      return true;
    });
  }
  
  // 7. Remove orphaned nodes after edge filtering (steps 5 & 6 may leave
  //    nodes that no longer have any visible edges). Always keep the focused node.
  if (filters.relationshipTypes.size > 0 || (filters.directionFilter && filters.directionFilter !== 'both')) {
    const connectedNodeIds = new Set<UUID>();
    edgeArray.forEach(e => {
      connectedNodeIds.add(e.source);
      connectedNodeIds.add(e.target);
    });
    if (filters.focusedNodeId) {
      connectedNodeIds.add(filters.focusedNodeId);
    }
    nodeArray = nodeArray.filter(n => connectedNodeIds.has(n.uuid!));
  }

  return {
    visibleNodes: nodeArray.map(n => n.uuid!),
    visibleEdges: edgeArray.map(e => e.id),
  };
}

/**
 * Filter minds to show only current version (highest version number per UUID)
 */
function filterCurrentVersions(minds: Mind[]): Mind[] {
  const latestVersions = new Map<UUID, Mind>();
  
  minds.forEach(mind => {
    const uuid = mind.uuid!;
    const existing = latestVersions.get(uuid);
    
    if (!existing || (mind.version ?? 0) > (existing.version ?? 0)) {
      latestVersions.set(uuid, mind);
    }
  });
  
  return Array.from(latestVersions.values());
}

// ============================================================================
// Reducer
// ============================================================================

/**
 * Helper function to add an action to history
 * Limits history size to maxSize and clears future stack
 */
function addToHistory(
  history: HistoryState,
  action: HistoryAction
): HistoryState {
  const newPast = [...history.past, action];
  
  // Limit history size
  if (newPast.length > history.maxSize) {
    newPast.shift(); // Remove oldest action
  }
  
  return {
    ...history,
    past: newPast,
    future: [], // Clear future stack when new action is performed
  };
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_MINDS': {
      // Filter to current versions only
      const currentVersions = filterCurrentVersions(action.payload);
      const mindsMap = new Map(currentVersions.map(m => [m.uuid!, m]));
      const { visibleNodes, visibleEdges } = applyFilters(mindsMap, state.relationships, state.filters);
      
      return {
        ...state,
        minds: mindsMap,
        visibleNodes,
        visibleEdges,
        canUndo: state.history.past.length > 0,
        canRedo: state.history.future.length > 0,
      };
    }
    
    case 'SET_RELATIONSHIPS': {
      const relationshipsMap = new Map(action.payload.map(r => [r.id, r]));
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, relationshipsMap, state.filters);
      
      return {
        ...state,
        relationships: relationshipsMap,
        visibleNodes,
        visibleEdges,
        canUndo: state.history.past.length > 0,
        canRedo: state.history.future.length > 0,
      };
    }
    
    case 'ADD_MIND': {
      const newMinds = new Map(state.minds);
      newMinds.set(action.payload.uuid!, action.payload);
      const { visibleNodes, visibleEdges } = applyFilters(newMinds, state.relationships, state.filters);
      
      // Track in history (no previous data for create)
      const newHistory = addToHistory(state.history, {
        type: 'create',
        entityType: 'mind',
        entityId: action.payload.uuid!,
        previousData: null,
      });
      
      return {
        ...state,
        minds: newMinds,
        visibleNodes,
        visibleEdges,
        history: newHistory,
        canUndo: newHistory.past.length > 0,
        canRedo: newHistory.future.length > 0,
      };
    }
    
    case 'UPDATE_MIND': {
      const previousMind = state.minds.get(action.payload.uuid!);
      const newMinds = new Map(state.minds);
      newMinds.set(action.payload.uuid!, action.payload);
      const { visibleNodes, visibleEdges } = applyFilters(newMinds, state.relationships, state.filters);
      
      // Track in history (store previous state for undo)
      const newHistory = addToHistory(state.history, {
        type: 'update',
        entityType: 'mind',
        entityId: action.payload.uuid!,
        previousData: previousMind,
      });
      
      return {
        ...state,
        minds: newMinds,
        visibleNodes,
        visibleEdges,
        history: newHistory,
        canUndo: newHistory.past.length > 0,
        canRedo: newHistory.future.length > 0,
      };
    }
    
    case 'DELETE_MIND': {
      const deletedMind = state.minds.get(action.payload);
      const newMinds = new Map(state.minds);
      newMinds.delete(action.payload);
      
      // Remove relationships connected to deleted node
      const newRelationships = new Map(state.relationships);
      Array.from(newRelationships.values())
        .filter(r => r.source === action.payload || r.target === action.payload)
        .forEach(r => newRelationships.delete(r.id));
      
      const { visibleNodes, visibleEdges } = applyFilters(newMinds, newRelationships, state.filters);
      
      // Track in history (store deleted mind for undo)
      const newHistory = addToHistory(state.history, {
        type: 'delete',
        entityType: 'mind',
        entityId: action.payload,
        previousData: deletedMind,
      });
      
      return {
        ...state,
        minds: newMinds,
        relationships: newRelationships,
        visibleNodes,
        visibleEdges,
        selection: {
          ...state.selection,
          selectedNodeId: state.selection.selectedNodeId === action.payload ? null : state.selection.selectedNodeId,
        },
        history: newHistory,
        canUndo: newHistory.past.length > 0,
        canRedo: newHistory.future.length > 0,
      };
    }
    
    case 'ADD_RELATIONSHIP': {
      const newRelationships = new Map(state.relationships);
      newRelationships.set(action.payload.id, action.payload);
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, newRelationships, state.filters);
      
      // Track in history (no previous data for create)
      const newHistory = addToHistory(state.history, {
        type: 'create',
        entityType: 'relationship',
        entityId: action.payload.id,
        previousData: null,
      });
      
      return {
        ...state,
        relationships: newRelationships,
        visibleNodes,
        visibleEdges,
        history: newHistory,
        canUndo: newHistory.past.length > 0,
        canRedo: newHistory.future.length > 0,
      };
    }
    
    case 'UPDATE_RELATIONSHIP': {
      const previousRelationship = state.relationships.get(action.payload.id);
      const newRelationships = new Map(state.relationships);
      newRelationships.set(action.payload.id, action.payload);
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, newRelationships, state.filters);
      
      // Track in history (store previous state for undo)
      const newHistory = addToHistory(state.history, {
        type: 'update',
        entityType: 'relationship',
        entityId: action.payload.id,
        previousData: previousRelationship,
      });
      
      return {
        ...state,
        relationships: newRelationships,
        visibleNodes,
        visibleEdges,
        history: newHistory,
        canUndo: newHistory.past.length > 0,
        canRedo: newHistory.future.length > 0,
      };
    }
    
    case 'DELETE_RELATIONSHIP': {
      const deletedRelationship = state.relationships.get(action.payload);
      const newRelationships = new Map(state.relationships);
      newRelationships.delete(action.payload);
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, newRelationships, state.filters);
      
      // Track in history (store deleted relationship for undo)
      const newHistory = addToHistory(state.history, {
        type: 'delete',
        entityType: 'relationship',
        entityId: action.payload,
        previousData: deletedRelationship,
      });
      
      return {
        ...state,
        relationships: newRelationships,
        visibleNodes,
        visibleEdges,
        selection: {
          ...state.selection,
          selectedEdgeId: state.selection.selectedEdgeId === action.payload ? null : state.selection.selectedEdgeId,
        },
        history: newHistory,
        canUndo: newHistory.past.length > 0,
        canRedo: newHistory.future.length > 0,
      };
    }
    
    case 'SET_NODE_TYPE_FILTER': {
      const newFilters = { ...state.filters, nodeTypes: action.payload };
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, state.relationships, newFilters);
      
      return {
        ...state,
        filters: newFilters,
        visibleNodes,
        visibleEdges,
      };
    }
    
    case 'SET_TEXT_SEARCH': {
      const newFilters = { ...state.filters, textSearch: action.payload };
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, state.relationships, newFilters);
      
      return {
        ...state,
        filters: newFilters,
        visibleNodes,
        visibleEdges,
      };
    }
    
    case 'SET_LEVEL': {
      const newFilters = { ...state.filters, level: action.payload };
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, state.relationships, newFilters);
      
      return {
        ...state,
        filters: newFilters,
        visibleNodes,
        visibleEdges,
      };
    }
    
    case 'SET_FOCUS_MODE': {
      const newFilters = { ...state.filters, focusedNodeId: action.payload };
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, state.relationships, newFilters);
      
      return {
        ...state,
        filters: newFilters,
        visibleNodes,
        visibleEdges,
      };
    }
    
    case 'RESET_FILTERS': {
      const newFilters: FilterState = {
        nodeTypes: new Set(),
        textSearch: '',
        level: 0,
        focusedNodeId: null,
        relationshipTypes: new Set(),
        directionFilter: null,
      };
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, state.relationships, newFilters);
      
      return {
        ...state,
        filters: newFilters,
        visibleNodes,
        visibleEdges,
      };
    }
    
    case 'SELECT_NODE': {
      return {
        ...state,
        selection: {
          selectedNodeId: action.payload,
          selectedEdgeId: null, // Clear edge selection when selecting node
        },
      };
    }
    
    case 'SELECT_EDGE': {
      return {
        ...state,
        selection: {
          selectedNodeId: null, // Clear node selection when selecting edge
          selectedEdgeId: action.payload,
        },
      };
    }
    
    case 'SET_LAYOUT_ALGORITHM': {
      return {
        ...state,
        layout: {
          ...state.layout,
          algorithm: action.payload,
        },
      };
    }
    
    case 'SET_LAYOUT_DISTANCE': {
      return {
        ...state,
        layout: {
          ...state.layout,
          distance: action.payload,
        },
      };
    }
    
    case 'UNDO': {
      if (state.history.past.length === 0) {
        return state; // Nothing to undo
      }
      
      // Get the last action from past
      const lastAction = state.history.past[state.history.past.length - 1];
      const newPast = state.history.past.slice(0, -1);
      
      // Create inverse action for future stack
      let currentData: Mind | Relationship | undefined;
      if (lastAction.entityType === 'mind') {
        currentData = state.minds.get(lastAction.entityId);
      } else {
        currentData = state.relationships.get(lastAction.entityId);
      }
      
      const inverseAction: HistoryAction = {
        type: lastAction.type === 'create' ? 'delete' : lastAction.type === 'delete' ? 'create' : 'update',
        entityType: lastAction.entityType,
        entityId: lastAction.entityId,
        previousData: currentData,
      };
      
      const newFuture = [...state.history.future, inverseAction];
      
      // Apply the undo
      let newMinds = new Map(state.minds);
      let newRelationships = new Map(state.relationships);
      
      if (lastAction.entityType === 'mind') {
        if (lastAction.type === 'create') {
          // Undo create: delete the mind
          newMinds.delete(lastAction.entityId);
        } else if (lastAction.type === 'delete') {
          // Undo delete: restore the mind
          if (lastAction.previousData) {
            newMinds.set(lastAction.entityId, lastAction.previousData as Mind);
          }
        } else if (lastAction.type === 'update') {
          // Undo update: restore previous state
          if (lastAction.previousData) {
            newMinds.set(lastAction.entityId, lastAction.previousData as Mind);
          }
        }
      } else {
        if (lastAction.type === 'create') {
          // Undo create: delete the relationship
          newRelationships.delete(lastAction.entityId);
        } else if (lastAction.type === 'delete') {
          // Undo delete: restore the relationship
          if (lastAction.previousData) {
            newRelationships.set(lastAction.entityId, lastAction.previousData as Relationship);
          }
        } else if (lastAction.type === 'update') {
          // Undo update: restore previous state
          if (lastAction.previousData) {
            newRelationships.set(lastAction.entityId, lastAction.previousData as Relationship);
          }
        }
      }
      
      const { visibleNodes, visibleEdges } = applyFilters(newMinds, newRelationships, state.filters);
      
      return {
        ...state,
        minds: newMinds,
        relationships: newRelationships,
        visibleNodes,
        visibleEdges,
        history: {
          ...state.history,
          past: newPast,
          future: newFuture,
        },
        canUndo: newPast.length > 0,
        canRedo: newFuture.length > 0,
      };
    }
    
    case 'REDO': {
      if (state.history.future.length === 0) {
        return state; // Nothing to redo
      }
      
      // Get the last action from future
      const lastAction = state.history.future[state.history.future.length - 1];
      const newFuture = state.history.future.slice(0, -1);
      
      // Create inverse action for past stack
      let currentData: Mind | Relationship | undefined;
      if (lastAction.entityType === 'mind') {
        currentData = state.minds.get(lastAction.entityId);
      } else {
        currentData = state.relationships.get(lastAction.entityId);
      }
      
      const inverseAction: HistoryAction = {
        type: lastAction.type === 'create' ? 'delete' : lastAction.type === 'delete' ? 'create' : 'update',
        entityType: lastAction.entityType,
        entityId: lastAction.entityId,
        previousData: currentData,
      };
      
      const newPast = [...state.history.past, inverseAction];
      
      // Apply the redo - the future stack contains the inverse of what we want to redo
      // So we need to reverse the inverse action
      let newMinds = new Map(state.minds);
      let newRelationships = new Map(state.relationships);
      
      if (lastAction.entityType === 'mind') {
        if (lastAction.type === 'delete') {
          // Future has delete, so redo means create (restore)
          if (lastAction.previousData) {
            newMinds.set(lastAction.entityId, lastAction.previousData as Mind);
          }
        } else if (lastAction.type === 'create') {
          // Future has create, so redo means delete
          newMinds.delete(lastAction.entityId);
        } else if (lastAction.type === 'update') {
          // Future has update with previous state, apply it
          if (lastAction.previousData) {
            newMinds.set(lastAction.entityId, lastAction.previousData as Mind);
          }
        }
      } else {
        if (lastAction.type === 'delete') {
          // Future has delete, so redo means create (restore)
          if (lastAction.previousData) {
            newRelationships.set(lastAction.entityId, lastAction.previousData as Relationship);
          }
        } else if (lastAction.type === 'create') {
          // Future has create, so redo means delete
          newRelationships.delete(lastAction.entityId);
        } else if (lastAction.type === 'update') {
          // Future has update with previous state, apply it
          if (lastAction.previousData) {
            newRelationships.set(lastAction.entityId, lastAction.previousData as Relationship);
          }
        }
      }
      
      const { visibleNodes, visibleEdges } = applyFilters(newMinds, newRelationships, state.filters);
      
      return {
        ...state,
        minds: newMinds,
        relationships: newRelationships,
        visibleNodes,
        visibleEdges,
        history: {
          ...state.history,
          past: newPast,
          future: newFuture,
        },
        canUndo: newPast.length > 0,
        canRedo: newFuture.length > 0,
      };
    }
    
    case 'SET_FAST_ADD_ENABLED': {
      if (action.payload) {
        return {
          ...state,
          fastAdd: { ...state.fastAdd, enabled: true },
        };
      }
      // Disabling: reset pre-selections to defaults (Req 1.1, 1.4)
      return {
        ...state,
        fastAdd: {
          enabled: false,
          selectedMindType: null,
          selectedRelationshipType: null,
          relationDirection: 'source',
        },
      };
    }

    case 'SET_FAST_ADD_MIND_TYPE': {
      return {
        ...state,
        fastAdd: { ...state.fastAdd, selectedMindType: action.payload },
      };
    }

    case 'SET_FAST_ADD_RELATIONSHIP_TYPE': {
      return {
        ...state,
        fastAdd: { ...state.fastAdd, selectedRelationshipType: action.payload },
      };
    }

    case 'SET_FAST_ADD_DIRECTION': {
      return {
        ...state,
        fastAdd: { ...state.fastAdd, relationDirection: action.payload },
      };
    }

    case 'SET_PICK_MODE': {
      return {
        ...state,
        pickMode: action.payload,
      };
    }

    case 'SET_FILTER_PANEL_COLLAPSED': {
      return {
        ...state,
        filterPanelCollapsed: action.payload,
      };
    }

    case 'SET_RELATIONSHIP_TYPE_FILTER': {
      const newFilters = { ...state.filters, relationshipTypes: action.payload };
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, state.relationships, newFilters);
      return {
        ...state,
        filters: newFilters,
        visibleNodes,
        visibleEdges,
      };
    }

    case 'SET_DIRECTION_FILTER': {
      const newFilters = { ...state.filters, directionFilter: action.payload };
      const { visibleNodes, visibleEdges } = applyFilters(state.minds, state.relationships, newFilters);
      return {
        ...state,
        filters: newFilters,
        visibleNodes,
        visibleEdges,
      };
    }

    case 'SET_LOADING': {
      return {
        ...state,
        loading: action.payload,
      };
    }
    
    case 'SET_ERROR': {
      return {
        ...state,
        error: action.payload,
      };
    }
    
    default:
      return state;
  }
}

// ============================================================================
// Context
// ============================================================================

interface GraphEditorContextValue {
  state: AppState;
  dispatch: React.Dispatch<Action>;
}

const GraphEditorContext = createContext<GraphEditorContextValue | undefined>(undefined);

// ============================================================================
// Provider
// ============================================================================

interface GraphEditorProviderProps {
  children: ReactNode;
  initialMinds?: Mind[];
  initialRelationships?: Relationship[];
  initialFocusedNodeId?: UUID | null;
}

export function GraphEditorProvider({ 
  children, 
  initialMinds = [],
  initialRelationships = [],
  initialFocusedNodeId = null
}: GraphEditorProviderProps) {
  // Create initial state with test data if provided
  const testInitialState: AppState = {
    ...initialState,
    minds: new Map(initialMinds.map(m => [m.uuid!, m])),
    relationships: new Map(initialRelationships.map(r => [r.id, r])),
    filters: {
      ...initialState.filters,
      focusedNodeId: initialFocusedNodeId,
    },
  };
  
  // Compute initial visible nodes/edges
  const filtered = applyFilters(
    testInitialState.minds,
    testInitialState.relationships,
    testInitialState.filters
  );
  testInitialState.visibleNodes = filtered.visibleNodes;
  testInitialState.visibleEdges = filtered.visibleEdges;
  
  const [state, dispatch] = useReducer(
    reducer, 
    initialMinds.length > 0 || initialRelationships.length > 0 || initialFocusedNodeId !== null
      ? testInitialState 
      : initialState
  );
  
  const value = useMemo(() => ({ state, dispatch }), [state]);
  
  return (
    <GraphEditorContext.Provider value={value}>
      {children}
    </GraphEditorContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Custom hook to access GraphEditor context
 * Throws error if used outside of GraphEditorProvider
 */
export function useGraphEditor(): GraphEditorContextValue {
  const context = useContext(GraphEditorContext);
  
  if (context === undefined) {
    throw new Error('useGraphEditor must be used within a GraphEditorProvider');
  }
  
  return context;
}
