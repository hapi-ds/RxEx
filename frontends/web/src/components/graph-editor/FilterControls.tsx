/**
 * FilterControls Component
 * Provides UI for filtering the graph by node type, text search, and proximity level
 * 
 * Features:
 * - Multi-select dropdown for node types
 * - Display count for each node type
 * - Text search input with debouncing (300ms)
 * - Proximity level slider (0-5 hops)
 * - Collapsible panel with chevron toggle
 * - Wire to state management
 * 
 * Performance Optimizations:
 * - Wrapped with React.memo to prevent unnecessary re-renders
 * - Event handlers use useCallback for stable references
 * - Text search debounced to 300ms to prevent excessive updates
 * 
 * **Validates: Requirements 2.1, 2.2, 2.3, 2.6, 2.7, 2.9, 2.10, 5.1, 5.2, 5.3, 5.4, 5.5, 9.11**
 */

import { useMemo, useState, useEffect, useRef, memo, useCallback } from 'react';
import { useGraphEditor, type NodeType, type RelationshipType } from './GraphEditorContext';
import { NODE_TYPE_CONFIGS } from './nodeTypeConfig';
import { useScreenReaderAnnouncer } from './ScreenReaderAnnouncer';
import { mindTypeToNodeType } from '../../utils/mindTypeUtils';
import './FilterControls.css';

// Internal scheduling artifacts that should not appear in the filter dropdown
const HIDDEN_NODE_TYPES: NodeType[] = ['ScheduleHistory', 'ScheduledTask'];

/**
 * FilterControls Component
 * Multi-select dropdown for filtering nodes by type and text search
 * Supports collapse/expand via chevron toggle (Req 5.1-5.5)
 */
export const FilterControls = memo(function FilterControls() {
  const { state, dispatch } = useGraphEditor();
  const { filters, minds, filterPanelCollapsed, fastAdd } = state;
  const { announceFilterChange } = useScreenReaderAnnouncer();

  // Local state for text search input (before debouncing)
  const [searchInputValue, setSearchInputValue] = useState(filters.textSearch);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync local state with context state when it changes externally (e.g., reset filters)
  useEffect(() => {
    setSearchInputValue(filters.textSearch);
  }, [filters.textSearch]);

  // Toggle collapse/expand
  const handleToggleCollapse = useCallback(() => {
    dispatch({ type: 'SET_FILTER_PANEL_COLLAPSED', payload: !filterPanelCollapsed });
  }, [dispatch, filterPanelCollapsed]);

  // Calculate count for each node type
  const nodeTypeCounts = useMemo(() => {
    const counts = new Map<NodeType, number>();
    
    // Initialize visible node types with 0 (exclude hidden scheduling types)
    const visibleNodeTypes = (Object.keys(NODE_TYPE_CONFIGS) as NodeType[]).filter(
      type => !HIDDEN_NODE_TYPES.includes(type)
    );
    visibleNodeTypes.forEach(type => counts.set(type, 0));
    
    // Count current version minds by type
    const currentVersionMinds = Array.from(minds.values());
    const mindsByUuid = new Map<string, typeof currentVersionMinds[0]>();
    
    // Keep only highest version for each UUID
    currentVersionMinds.forEach(mind => {
      const existing = mindsByUuid.get(mind.uuid!);
      if (!existing || mind.version! > existing.version!) {
        mindsByUuid.set(mind.uuid!, mind);
      }
    });
    
    // Count by type - use mind_type from backend and capitalize it
    mindsByUuid.forEach(mind => {
      // Backend returns lowercase mind_type, frontend expects capitalized NodeType
      const type = mindTypeToNodeType((mind as any).mind_type) as NodeType;
      if (type) {
        counts.set(type, (counts.get(type) || 0) + 1);
      }
    });
    
    return counts;
  }, [minds]);

  // Handle node type selection toggle
  const handleNodeTypeToggle = useCallback((nodeType: NodeType) => {
    const newSelectedTypes = new Set(filters.nodeTypes);
    
    if (newSelectedTypes.has(nodeType)) {
      newSelectedTypes.delete(nodeType);
    } else {
      newSelectedTypes.add(nodeType);
    }
    
    dispatch({ type: 'SET_NODE_TYPE_FILTER', payload: newSelectedTypes });
    
    // Announce filter change
    const config = NODE_TYPE_CONFIGS[nodeType];
    const action = newSelectedTypes.has(nodeType) ? 'added' : 'removed';
    announceFilterChange('Node type filter', `${config.label} ${action}`);
  }, [filters.nodeTypes, dispatch, announceFilterChange]);

  // Handle select all
  const handleSelectAll = useCallback(() => {
    // Filter out hidden node types when selecting all
    const visibleNodeTypes = (Object.keys(NODE_TYPE_CONFIGS) as NodeType[]).filter(
      type => !HIDDEN_NODE_TYPES.includes(type)
    );
    dispatch({ type: 'SET_NODE_TYPE_FILTER', payload: new Set(visibleNodeTypes) });
    
    // Announce filter change
    announceFilterChange('Node type filter', 'all types selected');
  }, [dispatch, announceFilterChange]);

  // Handle clear all
  const handleClearAll = useCallback(() => {
    dispatch({ type: 'SET_NODE_TYPE_FILTER', payload: new Set() });
    
    // Announce filter change
    announceFilterChange('Node type filter', 'all types cleared');
  }, [dispatch, announceFilterChange]);

  // Handle text search input change with debouncing (300ms)
  const handleSearchInputChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchInputValue(value);

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer to dispatch after 300ms
    debounceTimerRef.current = setTimeout(() => {
      dispatch({ type: 'SET_TEXT_SEARCH', payload: value });
      
      // Announce filter change
      if (value) {
        announceFilterChange('Text search applied', `searching for "${value}"`);
      } else {
        announceFilterChange('Text search', 'cleared');
      }
    }, 300);
  }, [dispatch, announceFilterChange]);

  // Handle clear search button
  const handleClearSearch = useCallback(() => {
    setSearchInputValue('');
    dispatch({ type: 'SET_TEXT_SEARCH', payload: '' });
    
    // Clear any pending debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Announce filter change
    announceFilterChange('Text search', 'cleared');
  }, [dispatch, announceFilterChange]);

  // Handle level slider change
  const handleLevelChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(event.target.value, 10);
    dispatch({ type: 'SET_LEVEL', payload: value });
    
    // Announce filter change
    const hops = value === 1 ? 'hop' : 'hops';
    announceFilterChange('Proximity level changed', `${value} ${hops}`);
  }, [dispatch, announceFilterChange]);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Filter out internal scheduling artifacts from the filter dropdown
  const allNodeTypes = (Object.keys(NODE_TYPE_CONFIGS) as NodeType[]).filter(
    type => !HIDDEN_NODE_TYPES.includes(type)
  );
  const selectedCount = filters.nodeTypes.size;
  const totalCount = allNodeTypes.length;

  // All available relationship types for the Fast Add selector
  const allRelationshipTypes: RelationshipType[] = [
    'PREVIOUS', 'SCHEDULED', 'CONTAINS', 'PREDATES', 'ASSIGNED_TO',
    'DEPENDS_ON', 'RELATES_TO', 'IMPLEMENTS', 'MITIGATES', 'TO',
    'FOR', 'REFINES', 'HAS_SCHEDULED', 'CAN_OCCUR', 'LEAD_TO',
  ];

  // Fast Add Mode handlers
  const handleFastAddToggle = useCallback(() => {
    dispatch({ type: 'SET_FAST_ADD_ENABLED', payload: !fastAdd.enabled });
  }, [dispatch, fastAdd.enabled]);

  const handleMindTypeChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    dispatch({ type: 'SET_FAST_ADD_MIND_TYPE', payload: value ? (value as NodeType) : null });
  }, [dispatch]);

  const handleRelationshipTypeChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    dispatch({ type: 'SET_FAST_ADD_RELATIONSHIP_TYPE', payload: value ? (value as RelationshipType) : null });
  }, [dispatch]);

  const handleDirectionChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    dispatch({ type: 'SET_FAST_ADD_DIRECTION', payload: event.target.value as 'source' | 'target' });
  }, [dispatch]);

  // Relationship type filter handlers (Req 6.1, 6.5, 6.6)
  const handleRelationshipTypeFilterToggle = useCallback((relType: RelationshipType) => {
    const newSelected = new Set(filters.relationshipTypes);
    if (newSelected.has(relType)) {
      newSelected.delete(relType);
    } else {
      newSelected.add(relType);
    }
    dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: newSelected });
    const action = newSelected.has(relType) ? 'added' : 'removed';
    announceFilterChange('Relationship type filter', `${relType} ${action}`);
  }, [filters.relationshipTypes, dispatch, announceFilterChange]);

  const handleRelationshipFilterSelectAll = useCallback(() => {
    dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: new Set(allRelationshipTypes) });
    announceFilterChange('Relationship type filter', 'all types selected');
  }, [dispatch, allRelationshipTypes, announceFilterChange]);

  const handleRelationshipFilterClearAll = useCallback(() => {
    dispatch({ type: 'SET_RELATIONSHIP_TYPE_FILTER', payload: new Set() });
    announceFilterChange('Relationship type filter', 'all types cleared');
  }, [dispatch, announceFilterChange]);

  // Direction filter handler (Req 6.2)
  const handleDirectionFilterChange = useCallback((value: 'outgoing' | 'incoming' | 'both' | null) => {
    dispatch({ type: 'SET_DIRECTION_FILTER', payload: value });
    announceFilterChange('Direction filter', value ?? 'cleared');
  }, [dispatch, announceFilterChange]);

  // Check if any filters are active (different from defaults)
  // Use local searchInputValue instead of filters.textSearch to detect typing immediately
  const hasActiveFilters = 
    filters.nodeTypes.size > 0 ||
    searchInputValue !== '' ||
    filters.level !== 0 ||
    filters.focusedNodeId !== null ||
    filters.relationshipTypes.size > 0 ||
    (filters.directionFilter !== null && filters.directionFilter !== 'both');

  // Handle reset filters
  const handleResetFilters = useCallback(() => {
    // Clear any pending debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    dispatch({ type: 'RESET_FILTERS' });
    
    // Announce filter change
    announceFilterChange('All filters', 'reset to default');
  }, [dispatch, announceFilterChange]);

  return (
    <div className={`filter-controls-wrapper ${filterPanelCollapsed ? 'collapsed' : 'expanded'}`}>
      {/* Collapse/Expand Toggle Button (Req 5.1) */}
      <button
        type="button"
        className="filter-panel-toggle"
        onClick={handleToggleCollapse}
        aria-label={filterPanelCollapsed ? 'Expand filter panel' : 'Collapse filter panel'}
        aria-expanded={!filterPanelCollapsed}
        title={filterPanelCollapsed ? 'Expand filters' : 'Collapse filters'}
      >
        <span className="filter-panel-toggle-icon">
          {filterPanelCollapsed ? '▶' : '◀'}
        </span>
      </button>

      {/* Filter panel content - hidden when collapsed (Req 5.2, 5.3) */}
      {!filterPanelCollapsed && (
        <div className="filter-controls">
          {/* Reset Filters Button */}
          <div className="filter-section">
            <button
              type="button"
              className="reset-filters-button"
              onClick={handleResetFilters}
              disabled={!hasActiveFilters}
              aria-label="Reset all filters"
              title="Clear all filters and return to default view"
            >
              Reset Filters
            </button>
          </div>

          {/* Fast Add Mode Section (Req 1.1, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4) */}
          <div className={`fast-add-section ${fastAdd.enabled ? 'active' : ''}`}>
            <div className="fast-add-toggle">
              <span className="fast-add-toggle-label">Fast Add Mode</span>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={fastAdd.enabled}
                  onChange={handleFastAddToggle}
                  aria-label="Toggle Fast Add Mode"
                />
                <span className="toggle-slider" />
              </label>
            </div>

            {fastAdd.enabled && (
              <div className="fast-add-controls">
                {/* Mind Type Selector (Req 2.1, 2.2, 2.3) */}
                <div className="fast-add-control-group">
                  <label className="fast-add-control-label" htmlFor="fast-add-mind-type">
                    Mind Type
                  </label>
                  <select
                    id="fast-add-mind-type"
                    className="fast-add-select"
                    value={fastAdd.selectedMindType ?? ''}
                    onChange={handleMindTypeChange}
                    aria-label="Select mind type for fast add"
                  >
                    <option value="">-- Select Mind Type --</option>
                    {allNodeTypes.map(nodeType => {
                      const config = NODE_TYPE_CONFIGS[nodeType];
                      return (
                        <option key={nodeType} value={nodeType}>
                          {config.label}
                        </option>
                      );
                    })}
                  </select>
                </div>

                {/* Relationship Type Selector (Req 3.1) */}
                <div className="fast-add-control-group">
                  <label className="fast-add-control-label" htmlFor="fast-add-relationship-type">
                    Relationship Type
                  </label>
                  <select
                    id="fast-add-relationship-type"
                    className="fast-add-select"
                    value={fastAdd.selectedRelationshipType ?? ''}
                    onChange={handleRelationshipTypeChange}
                    aria-label="Select relationship type for fast add"
                  >
                    <option value="">-- Select Relationship Type --</option>
                    {allRelationshipTypes.map(relType => (
                      <option key={relType} value={relType}>
                        {relType}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Direction Selector (Req 3.2, 3.3, 3.4) */}
                <div className="fast-add-control-group">
                  <label className="fast-add-control-label" htmlFor="fast-add-direction">
                    Direction
                  </label>
                  <select
                    id="fast-add-direction"
                    className="fast-add-select"
                    value={fastAdd.relationDirection}
                    onChange={handleDirectionChange}
                    aria-label="Select relationship direction for fast add"
                  >
                    <option value="source">Clicked node is source</option>
                    <option value="target">Clicked node is target</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Text Search Section */}
          <div className="filter-section">
            <h3 className="filter-section-title">Search by Title</h3>
            <div className="text-search-container">
              <input
                type="text"
                className="text-search-input"
                placeholder="Search minds by title..."
                value={searchInputValue}
                onChange={handleSearchInputChange}
                aria-label="Search minds by title"
              />
              {searchInputValue && (
                <button
                  type="button"
                  className="text-search-clear"
                  onClick={handleClearSearch}
                  aria-label="Clear search"
                  title="Clear search"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Proximity Level Control Section */}
          <div className="filter-section">
            <div className="level-control-header">
              <h3 className="filter-section-title">Proximity Level</h3>
              <span className="level-control-value" aria-live="polite">
                {filters.level} {filters.level === 1 ? 'hop' : 'hops'}
              </span>
            </div>
            <div className="level-control-container">
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={filters.level}
                onChange={handleLevelChange}
                className="level-control-slider"
                aria-label="Proximity level in relationship hops"
                aria-valuemin={0}
                aria-valuemax={10}
                aria-valuenow={filters.level}
                aria-valuetext={`${filters.level} ${filters.level === 1 ? 'hop' : 'hops'}`}
              />
              <div className="level-control-labels">
                <span>0</span>
                <span>1</span>
                <span>2</span>
                <span>3</span>
                <span>4</span>
                <span>5</span>
                <span>6</span>
                <span>7</span>
                <span>8</span>
                <span>9</span>
                <span>10</span>
              </div>
            </div>
            <p className="level-control-help">
              Controls how many relationship hops away from matching nodes to include in search results
            </p>
          </div>

          {/* Node Type Filter Section */}
          <div className="filter-section">
            <div className="filter-controls-header">
              <h3>Filter by Node Type</h3>
              <div className="filter-controls-actions">
                <button
                  type="button"
                  onClick={handleSelectAll}
                  className="filter-action-button"
                  disabled={selectedCount === totalCount}
                  aria-label="Select all node types"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="filter-action-button"
                  disabled={selectedCount === 0}
                  aria-label="Clear all node type selections"
                >
                  Clear All
                </button>
              </div>
            </div>

            <div className="filter-controls-list" role="group" aria-label="Node type filters">
              {allNodeTypes.map(nodeType => {
                const config = NODE_TYPE_CONFIGS[nodeType];
                const count = nodeTypeCounts.get(nodeType) || 0;
                const isSelected = filters.nodeTypes.has(nodeType);

                return (
                  <label
                    key={nodeType}
                    className={`filter-control-item ${isSelected ? 'selected' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleNodeTypeToggle(nodeType)}
                      aria-label={`Filter ${config.label} nodes`}
                    />
                    <span className="filter-control-label">
                      {config.label}
                    </span>
                    <span className="filter-control-count" aria-label={`${count} nodes`}>
                      ({count})
                    </span>
                  </label>
                );
              })}
            </div>

            {selectedCount > 0 && (
              <div className="filter-controls-summary" aria-live="polite">
                {selectedCount} of {totalCount} node types selected
              </div>
            )}
          </div>

          {/* Relationship Type Filter Section (Req 6.1, 6.5, 6.6) */}
          <div className="filter-section">
            <div className="filter-controls-header">
              <h3>Filter by Relationship Type</h3>
              <div className="filter-controls-actions">
                <button
                  type="button"
                  onClick={handleRelationshipFilterSelectAll}
                  className="filter-action-button"
                  disabled={filters.relationshipTypes.size === allRelationshipTypes.length}
                  aria-label="Select all relationship types"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={handleRelationshipFilterClearAll}
                  className="filter-action-button"
                  disabled={filters.relationshipTypes.size === 0}
                  aria-label="Clear all relationship type selections"
                >
                  Clear All
                </button>
              </div>
            </div>

            <div className="filter-controls-list" role="group" aria-label="Relationship type filters">
              {allRelationshipTypes.map(relType => {
                const isSelected = filters.relationshipTypes.has(relType);
                return (
                  <label
                    key={relType}
                    className={`filter-control-item ${isSelected ? 'selected' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleRelationshipTypeFilterToggle(relType)}
                      aria-label={`Filter ${relType} relationships`}
                    />
                    <span className="filter-control-label">
                      {relType}
                    </span>
                  </label>
                );
              })}
            </div>

            {filters.relationshipTypes.size > 0 && (
              <div className="filter-controls-summary" aria-live="polite">
                {filters.relationshipTypes.size} of {allRelationshipTypes.length} relationship types selected
              </div>
            )}
          </div>

          {/* Direction Filter Section (Req 6.2, 6.6) */}
          <div className="filter-section">
            <h3 className="filter-section-title">Filter by Direction</h3>
            <div className="direction-filter-group" role="radiogroup" aria-label="Edge direction filter">
              {(['outgoing', 'incoming', 'both'] as const).map(direction => {
                const label = direction.charAt(0).toUpperCase() + direction.slice(1);
                const isSelected = filters.directionFilter === direction;
                return (
                  <label key={direction} className={`direction-filter-option ${isSelected ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name="direction-filter"
                      value={direction}
                      checked={isSelected}
                      onChange={() => handleDirectionFilterChange(direction)}
                      aria-label={`Show ${label.toLowerCase()} edges`}
                    />
                    <span className="direction-filter-label">{label}</span>
                  </label>
                );
              })}
              {filters.directionFilter !== null && (
                <button
                  type="button"
                  className="filter-action-button direction-filter-clear"
                  onClick={() => handleDirectionFilterChange(null)}
                  aria-label="Clear direction filter"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
});
