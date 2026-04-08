/**
 * GraphCanvas Component
 * Renders the interactive graph visualization using react-flow
 * 
 * Responsibilities:
 * - Render nodes and edges using react-flow
 * - Handle pan/zoom interactions
 * - Apply layout algorithm to position nodes
 * - Emit selection events
 * - Display hover tooltips
 * - Support keyboard navigation
 * 
 * Performance Optimizations:
 * - React Flow has built-in viewport-based rendering (virtualization)
 * - Only nodes visible in the viewport are rendered to the DOM
 * - Nodes and edges are memoized to prevent unnecessary re-renders
 * - Custom node components use React.memo for optimal performance
 * - Handles large graphs (1000+ nodes) efficiently
 * 
 * **Validates: Requirements 1.1, 1.6, 1.7, 1.8, 9.4, 9.10**
 */

import { useCallback, useEffect, useState, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  type Node,
  type Edge,
  type NodeChange,
  type EdgeChange,
  type Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';
import './GraphCanvas.css';
import { useGraphEditor, type UUID } from './GraphEditorContext';
import { useScreenReaderAnnouncer } from './ScreenReaderAnnouncer';
import type { Mind, Relationship } from './GraphEditorContext';
import { nodeTypes } from './nodes';
import { edgeTypes } from './edges';
import { LayoutControls } from './LayoutControls';
import { GraphToolbar } from './GraphToolbar';
import { FilterControls } from './FilterControls';
import { FocusModeBadge } from './FocusModeBadge';
import { getLayoutFunction } from './layouts';
import type { NodePosition } from './layouts';
import { Tooltip } from './Tooltip';
import { FastAddPrompt } from './FastAddPrompt';
import { FastAddIndicator } from './FastAddIndicator';
import { useToast } from './ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import { mindsAPI, relationshipsAPI } from '../../services/api';
import { mindTypeToNodeType } from '../../utils/mindTypeUtils';
import { getNodeTypeConfig } from './nodeTypeConfig';

/**
 * Convert Mind to ReactFlow Node
 */
function mindToNode(
  mind: Mind,
  isSelected: boolean,
  isFocused: boolean,
  onMouseEnter: (event: React.MouseEvent, nodeId: string) => void,
  onMouseLeave: () => void
): Node {
  const nodeType = mindTypeToNodeType((mind as any).mind_type);
  
  return {
    id: mind.uuid!,
    type: nodeType,
    position: { x: 0, y: 0 }, // Will be set by layout algorithm
    selected: isSelected,
    data: {
      label: mind.title,
      type: nodeType,
      mind,
      isFocused,
      onMouseEnter,
      onMouseLeave,
    },
  };
}

/**
 * Convert Relationship to ReactFlow Edge
 */
function relationshipToEdge(
  relationship: Relationship,
  isSelected: boolean,
  onMouseEnter: (event: React.MouseEvent, edgeId: string) => void,
  onMouseLeave: () => void
): Edge {
  return {
    id: relationship.id,
    source: relationship.source,
    target: relationship.target,
    type: 'custom', // Use custom edge type
    selected: isSelected,
    data: {
      type: relationship.type,
      relationship,
      onMouseEnter,
      onMouseLeave,
    },
  };
}

/**
 * GraphCanvas Component
 * Main graph visualization component using react-flow
 */
export function GraphCanvas() {
  const { state, dispatch } = useGraphEditor();
  const { announceFilterChange } = useScreenReaderAnnouncer();
  const { showError } = useToast();
  const { token } = useAuth();
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 });
  const [focusedNodeIndex, setFocusedNodeIndex] = useState<number>(-1);
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(new Map());
  
  // Tooltip state
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    content: React.ReactNode;
    x: number;
    y: number;
  }>({
    visible: false,
    content: null,
    x: 0,
    y: 0,
  });

  // Fast-add right-click state: tracks the right-clicked node and mouse position
  const [fastAddTarget, setFastAddTarget] = useState<{
    nodeId: string;
    position: { x: number; y: number };
  } | null>(null);

  // Handle node hover
  const handleNodeMouseEnter = useCallback((event: React.MouseEvent, nodeId: string) => {
    const mind = state.minds.get(nodeId as UUID);
    if (mind) {
      setTooltip({
        visible: true,
        content: (
          <div>
            <div className="tooltip-title">{mind.title}</div>
            <div className="tooltip-type">{mindTypeToNodeType((mind as any).mind_type)}</div>
          </div>
        ),
        x: event.clientX,
        y: event.clientY,
      });
    }
  }, [state.minds]);

  // Handle edge hover
  const handleEdgeMouseEnter = useCallback((event: React.MouseEvent, edgeId: string) => {
    const relationship = state.relationships.get(edgeId);
    if (relationship) {
      setTooltip({
        visible: true,
        content: (
          <div>
            <div className="tooltip-relationship-type">{relationship.type}</div>
          </div>
        ),
        x: event.clientX,
        y: event.clientY,
      });
    }
  }, [state.relationships]);

  // Handle mouse leave (hide tooltip)
  const handleMouseLeave = useCallback(() => {
    setTooltip(prev => ({ ...prev, visible: false }));
  }, []);

  // Update canvas size on mount and resize
  useEffect(() => {
    const updateSize = () => {
      const container = document.querySelector('.react-flow');
      if (container) {
        const rect = container.getBoundingClientRect();
        setCanvasSize({ width: rect.width, height: rect.height });
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Calculate layout positions when layout settings or visible nodes change
  useEffect(() => {
    if (state.visibleNodes.length === 0) {
      setNodePositions(new Map());
      return;
    }

    const layoutFunction = getLayoutFunction(state.layout.algorithm);
    
    // Get minds for layout calculation
    const mindsForLayout = state.visibleNodes
      .map(uuid => state.minds.get(uuid))
      .filter((mind): mind is Mind => mind !== undefined);
    
    // Get relationships for layout calculation
    const relationshipsForLayout = state.visibleEdges
      .map(id => state.relationships.get(id))
      .filter((rel): rel is Relationship => rel !== undefined);
    
    // Calculate positions using the selected layout algorithm
    const positions: NodePosition[] = layoutFunction(
      mindsForLayout,
      relationshipsForLayout,
      state.layout.distance,
      canvasSize.width,
      canvasSize.height
    );

    // Store positions in a map
    const positionMap = new Map(positions.map(p => [p.id, { x: p.x, y: p.y }]));
    setNodePositions(positionMap);
  }, [
    state.layout.algorithm,
    state.layout.distance,
    state.visibleNodes,
    state.visibleEdges,
    state.minds,
    state.relationships,
    canvasSize,
  ]);

  // Convert visible minds to nodes with calculated positions
  // Memoized to prevent unnecessary re-renders and optimize performance for large graphs
  const nodes: Node[] = useMemo(() => {
    return state.visibleNodes
      .map(uuid => state.minds.get(uuid))
      .filter((mind): mind is Mind => mind !== undefined)
      .map(mind => {
        const node = mindToNode(
          mind,
          state.selection.selectedNodeId === mind.uuid,
          state.filters.focusedNodeId === mind.uuid,
          handleNodeMouseEnter,
          handleMouseLeave
        );
        
        // Apply calculated position if available
        const position = nodePositions.get(mind.uuid!);
        if (position) {
          node.position = position;
        }
        
        return node;
      });
  }, [
    state.visibleNodes,
    state.minds,
    state.selection.selectedNodeId,
    state.filters.focusedNodeId,
    nodePositions,
    handleNodeMouseEnter,
    handleMouseLeave,
  ]);

  // Convert visible relationships to edges
  // Memoized to prevent unnecessary re-renders and optimize performance for large graphs
  const edges: Edge[] = useMemo(() => {
    return state.visibleEdges
      .map(id => state.relationships.get(id))
      .filter((rel): rel is Relationship => rel !== undefined)
      .map(rel => relationshipToEdge(
        rel,
        state.selection.selectedEdgeId === rel.id,
        handleEdgeMouseEnter,
        handleMouseLeave
      ));
  }, [
    state.visibleEdges,
    state.relationships,
    state.selection.selectedEdgeId,
    handleEdgeMouseEnter,
    handleMouseLeave,
  ]);

  // Handle node selection and focus mode
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      const nodeId = node.id as UUID;

      // Pick mode: intercept click to populate the relationship modal field (Req 8.5, 8.6)
      if (state.pickMode && state.pickMode.active) {
        // Dispatch custom event so CreateRelationshipModal can receive the picked node
        window.dispatchEvent(
          new CustomEvent('pick-mode-complete', {
            detail: { nodeId, field: state.pickMode.field },
          }),
        );
        // Exit pick mode
        dispatch({ type: 'SET_PICK_MODE', payload: null });
        return; // Don't select the node
      }
      
      // Check if Shift key is pressed for focus mode
      if (event.shiftKey) {
        // Toggle focus mode: if clicking on already focused node, exit focus mode
        if (state.filters.focusedNodeId === nodeId) {
          dispatch({ type: 'SET_FOCUS_MODE', payload: null });
          // Announcement handled by FocusModeBadge exit handler
        } else {
          const mind = state.minds.get(nodeId);
          dispatch({ type: 'SET_FOCUS_MODE', payload: nodeId });
          // Announce focus mode activation
          if (mind) {
            announceFilterChange('Focus mode activated', `on ${mind.title}`);
          }
        }
      } else {
        // Regular click: select node
        dispatch({ type: 'SELECT_NODE', payload: nodeId });
      }
    },
    [dispatch, state.filters.focusedNodeId, state.minds, state.pickMode, announceFilterChange]
  );

  // Handle edge selection
  const onEdgeClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      dispatch({ type: 'SELECT_EDGE', payload: edge.id });
    },
    [dispatch]
  );

  // Handle pane click (deselect)
  const onPaneClick = useCallback(() => {
    dispatch({ type: 'SELECT_NODE', payload: null });
  }, [dispatch]);

  // Handle right-click on a node for fast-add (Req 1.3, 1.4, 4.7, 7.1)
  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: Node) => {
      if (!state.fastAdd.enabled) {
        // Fast-add disabled: allow default browser context menu
        return;
      }

      // Only allow fast-add on nodes currently visible in the filtered graph (Req 7.1)
      if (!state.visibleNodes.includes(node.id as UUID)) {
        return;
      }

      // Prevent default context menu when fast-add is active
      event.preventDefault();

      // Capture the right-clicked node ID and mouse position
      setFastAddTarget({
        nodeId: node.id,
        position: { x: event.clientX, y: event.clientY },
      });
    },
    [state.fastAdd.enabled, state.visibleNodes]
  );

  // Handle FastAddPrompt cancel
  const handleFastAddCancel = useCallback(() => {
    setFastAddTarget(null);
  }, []);

  // Handle FastAddPrompt submit — creates mind + relationship via API (Req 4.1–4.6)
  const handleFastAddSubmit = useCallback(
    async (data: { title: string }) => {
      const { selectedMindType, selectedRelationshipType, relationDirection } = state.fastAdd;

      // Validate pre-selections are set (Req 2.2)
      if (!selectedMindType || !selectedRelationshipType || !fastAddTarget) {
        setFastAddTarget(null);
        return;
      }

      // Extract creator from JWT token (logged-in user)
      let creator = 'unknown';
      try {
        if (token) {
          const payload = JSON.parse(atob(token.split('.')[1]));
          creator = payload.sub || payload.email || 'unknown';
        }
      } catch {
        // fallback to 'unknown' if token decode fails
      }

      const clickedNodeId = fastAddTarget.nodeId;
      setFastAddTarget(null);

      // Build the mind creation payload matching CreateNodeForm pattern
      const config = getNodeTypeConfig(selectedMindType);
      const createData: Record<string, unknown> = {
        mind_type: config.type,
        title: data.title,
        creator,
        status: 'draft',
      };

      // Step 1: Create the mind (Req 4.1)
      let createdMind: Mind;
      try {
        createdMind = await mindsAPI.create(
          createData as Omit<Mind, 'uuid' | 'version' | 'created_at' | 'updated_at'>,
        );
      } catch (error) {
        // Mind creation failed — show error, leave graph unchanged (Req 4.5)
        const msg = error instanceof Error ? error.message : 'Failed to create mind';
        showError(msg);
        return;
      }

      const newMindUuid = createdMind.uuid!;

      // Step 2: Create the relationship (Req 4.2)
      try {
        const relPayload = {
          type: selectedRelationshipType,
          source: relationDirection === 'source' ? clickedNodeId : newMindUuid,
          target: relationDirection === 'source' ? newMindUuid : clickedNodeId,
          properties: {},
        };
        const createdRel = await relationshipsAPI.create(relPayload);

        // Both succeeded — update graph state (Req 4.3, 4.4)
        dispatch({ type: 'ADD_MIND', payload: createdMind });
        dispatch({ type: 'ADD_RELATIONSHIP', payload: createdRel });
        dispatch({ type: 'SELECT_NODE', payload: newMindUuid });
      } catch (error) {
        // Relationship failed but mind succeeded — add orphaned mind (Req 4.6)
        const msg = error instanceof Error ? error.message : 'Failed to create relationship';
        showError(msg);
        dispatch({ type: 'ADD_MIND', payload: createdMind });
        dispatch({ type: 'SELECT_NODE', payload: newMindUuid });
      }
    },
    [state.fastAdd, fastAddTarget, dispatch, showError, token],
  );

  // Handle node changes (for drag, position updates, etc.)
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      // Apply position changes from dragging
      changes.forEach(change => {
        if (change.type === 'position' && change.position && change.id) {
          setNodePositions(prev => {
            const next = new Map(prev);
            next.set(change.id, { x: change.position!.x, y: change.position!.y });
            return next;
          });
        }
      });
    },
    []
  );

  // Handle edge changes
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      // For now, we don't handle edge changes
      console.log('Edge changes:', changes);
    },
    []
  );

  // Handle connection (for creating new edges)
  const onConnect = useCallback(
    (connection: Connection) => {
      // This will be implemented in Phase 3 when we add relationship creation
      console.log('Connection:', connection);
    },
    []
  );

  // Build adjacency map for arrow key navigation
  const buildAdjacencyMap = useCallback(() => {
    const adjacencyMap = new Map<string, Set<string>>();
    
    // Initialize sets for all visible nodes
    state.visibleNodes.forEach(nodeId => {
      adjacencyMap.set(nodeId, new Set());
    });
    
    // Add connections from edges
    state.visibleEdges.forEach(edgeId => {
      const relationship = state.relationships.get(edgeId);
      if (relationship) {
        // Add bidirectional connections for navigation
        const sourceSet = adjacencyMap.get(relationship.source);
        const targetSet = adjacencyMap.get(relationship.target);
        
        if (sourceSet) sourceSet.add(relationship.target);
        if (targetSet) targetSet.add(relationship.source);
      }
    });
    
    return adjacencyMap;
  }, [state.visibleNodes, state.visibleEdges, state.relationships]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle keyboard navigation when graph canvas is focused
      const target = event.target as HTMLElement;
      if (!target.closest('.react-flow')) return;

      const visibleNodeIds = state.visibleNodes;
      if (visibleNodeIds.length === 0) return;

      // Tab key: cycle through nodes
      if (event.key === 'Tab') {
        event.preventDefault();
        
        if (event.shiftKey) {
          // Shift+Tab: previous node
          setFocusedNodeIndex(prev => {
            const newIndex = prev <= 0 ? visibleNodeIds.length - 1 : prev - 1;
            return newIndex;
          });
        } else {
          // Tab: next node
          setFocusedNodeIndex(prev => {
            const newIndex = prev >= visibleNodeIds.length - 1 ? 0 : prev + 1;
            return newIndex;
          });
        }
        return;
      }

      // Enter key: select focused node
      if (event.key === 'Enter') {
        if (focusedNodeIndex >= 0 && focusedNodeIndex < visibleNodeIds.length) {
          const nodeId = visibleNodeIds[focusedNodeIndex];
          dispatch({ type: 'SELECT_NODE', payload: nodeId });
        }
        return;
      }

      // Arrow keys: navigate between connected nodes
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
        event.preventDefault();
        
        if (focusedNodeIndex < 0 || focusedNodeIndex >= visibleNodeIds.length) {
          // No node focused, focus first node
          setFocusedNodeIndex(0);
          return;
        }

        const currentNodeId = visibleNodeIds[focusedNodeIndex];
        const adjacencyMap = buildAdjacencyMap();
        const connectedNodes = adjacencyMap.get(currentNodeId);
        
        if (!connectedNodes || connectedNodes.size === 0) {
          // No connected nodes, stay on current node
          return;
        }

        // Get positions of current and connected nodes
        const currentNode = nodes.find(n => n.id === currentNodeId);
        if (!currentNode) return;

        const connectedNodesList = Array.from(connectedNodes)
          .map(nodeId => nodes.find(n => n.id === nodeId))
          .filter((n): n is Node => n !== undefined);

        if (connectedNodesList.length === 0) return;

        // Find the best node to navigate to based on arrow direction
        let targetNode: Node | undefined;

        switch (event.key) {
          case 'ArrowUp':
            // Find node above (smallest y that is less than current y)
            targetNode = connectedNodesList
              .filter(n => n.position.y < currentNode.position.y)
              .sort((a, b) => b.position.y - a.position.y)[0];
            break;
          case 'ArrowDown':
            // Find node below (largest y that is greater than current y)
            targetNode = connectedNodesList
              .filter(n => n.position.y > currentNode.position.y)
              .sort((a, b) => a.position.y - b.position.y)[0];
            break;
          case 'ArrowLeft':
            // Find node to the left (smallest x that is less than current x)
            targetNode = connectedNodesList
              .filter(n => n.position.x < currentNode.position.x)
              .sort((a, b) => b.position.x - a.position.x)[0];
            break;
          case 'ArrowRight':
            // Find node to the right (largest x that is greater than current x)
            targetNode = connectedNodesList
              .filter(n => n.position.x > currentNode.position.x)
              .sort((a, b) => a.position.x - b.position.x)[0];
            break;
        }

        // If no node found in that direction, try any connected node
        if (!targetNode && connectedNodesList.length > 0) {
          targetNode = connectedNodesList[0];
        }

        if (targetNode) {
          const targetIndex = visibleNodeIds.indexOf(targetNode.id as UUID);
          if (targetIndex >= 0) {
            setFocusedNodeIndex(targetIndex);
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusedNodeIndex, state.visibleNodes, nodes, buildAdjacencyMap, dispatch]);

  // Cancel pick mode on Escape key (Req 8.7)
  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent): void => {
      if (event.key === 'Escape' && state.pickMode) {
        dispatch({ type: 'SET_PICK_MODE', payload: null });
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, [state.pickMode, dispatch]);

  // Update node data to include keyboard focus state
  // Memoized to prevent unnecessary re-renders
  const nodesWithKeyboardFocus = useMemo(() => {
    return nodes.map((node, index) => ({
      ...node,
      data: {
        ...node.data,
        hasKeyboardFocus: index === focusedNodeIndex,
      },
    }));
  }, [nodes, focusedNodeIndex]);

  const isPickModeActive = state.pickMode !== null && state.pickMode.active;

  return (
    <div
      className={`graph-canvas-wrapper${isPickModeActive ? ' graph-canvas-wrapper--pick-mode' : ''}`}
      style={{ width: '100%', height: '100%', position: 'relative' }}
    >      <div style={{ 
        position: 'absolute', 
        top: '1rem', 
        left: '1rem', 
        zIndex: 10,
        pointerEvents: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        maxWidth: '300px'
      }}
      role="region"
      aria-label="Graph controls"
      >
        <LayoutControls />
        <FilterControls />
      </div>
      <div style={{ 
        position: 'absolute', 
        top: '1rem', 
        right: '1rem', 
        zIndex: 10,
        pointerEvents: 'auto'
      }}
      role="toolbar"
      aria-label="Graph editing toolbar"
      >
        <GraphToolbar />
      </div>
      {state.filters.focusedNodeId && (
        <div style={{ 
          position: 'absolute', 
          top: '1rem', 
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 10,
          pointerEvents: 'auto',
          minWidth: '300px',
          maxWidth: '500px'
        }}>
          <FocusModeBadge />
        </div>
      )}
      <ReactFlow
        nodes={nodesWithKeyboardFocus}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeContextMenu={onNodeContextMenu}
        fitView={nodePositions.size > 0}
        attributionPosition="bottom-right"
        aria-label="Interactive graph canvas"
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
      {state.fastAdd.enabled && <FastAddIndicator />}
      <Tooltip
        visible={tooltip.visible}
        content={tooltip.content}
        x={tooltip.x}
        y={tooltip.y}
      />
      {fastAddTarget && (
        <FastAddPrompt
          position={fastAddTarget.position}
          onSubmit={handleFastAddSubmit}
          onCancel={handleFastAddCancel}
        />
      )}
    </div>
  );
}

/**
 * GraphCanvas with ReactFlowProvider wrapper
 * ReactFlow requires a provider for proper initialization
 */
export function GraphCanvasWithProvider() {
  return (
    <ReactFlowProvider>
      <GraphCanvas />
    </ReactFlowProvider>
  );
}
