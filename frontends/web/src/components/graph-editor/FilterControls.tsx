/**
 * FilterControls Component
 * Provides UI for filtering the graph by node type, text search, and proximity level
 * 
 * Features:
 * - Multi-select dropdown for node types
 * - Display count for each node type
 * - Text search input with debouncing (300ms)
 * - Proximity level slider (0-5 hops)
 * - Wire to state management
 * 
 * Performance Optimizations:
 * - Wrapped with React.memo to prevent unnecessary re-renders
 * - Event handlers use useCallback for stable references
 * - Text search debounced to 300ms to prevent excessive updates
 * 
 * **Validates: Requirements 2.1, 2.2, 2.3, 2.6, 2.7, 2.9, 2.10, 9.11**
 */

import { useMemo, useState, useEffect, useRef, memo, useCallback } from 'react';
import { useGraphEditor, type NodeType } from './GraphEditorContext';
import { NODE_TYPE_CONFIGS } from './nodeTypeConfig';
import { useScreenReaderAnnouncer } from './ScreenReaderAnnouncer';
import { mindTypeToNodeType } from '../../utils/mindTypeUtils';
import './FilterControls.css';

/**
 * FilterControls Component
 * Multi-select dropdown for filtering nodes by type and text search
 */
export const FilterControls = memo(function FilterControls() {
  const { state, dispatch } = useGraphEditor();
  const { filters, minds } = state;
  const { announceFilterChange } = useScreenReaderAnnouncer();

  // Local state for text search input (before debouncing)
  const [searchInputValue, setSearchInputValue] = useState(filters.textSearch);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync local state with context state when it changes externally (e.g., reset filters)
  useEffect(() => {
    setSearchInputValue(filters.textSearch);
  }, [filters.textSearch]);

  // Calculate count for each node type
  const nodeTypeCounts = useMemo(() => {
    const counts = new Map<NodeType, number>();
    
    // Initialize all node types with 0
    const allNodeTypes = Object.keys(NODE_TYPE_CONFIGS) as NodeType[];
    allNodeTypes.forEach(type => counts.set(type, 0));
    
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
    const allNodeTypes = Object.keys(NODE_TYPE_CONFIGS) as NodeType[];
    dispatch({ type: 'SET_NODE_TYPE_FILTER', payload: new Set(allNodeTypes) });
    
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

  const allNodeTypes = Object.keys(NODE_TYPE_CONFIGS) as NodeType[];
  const selectedCount = filters.nodeTypes.size;
  const totalCount = allNodeTypes.length;

  // Check if any filters are active (different from defaults)
  // Use local searchInputValue instead of filters.textSearch to detect typing immediately
  const hasActiveFilters = 
    filters.nodeTypes.size > 0 ||
    searchInputValue !== '' ||
    filters.level !== 0 ||
    filters.focusedNodeId !== null;

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
            max="5"
            step="1"
            value={filters.level}
            onChange={handleLevelChange}
            className="level-control-slider"
            aria-label="Proximity level in relationship hops"
            aria-valuemin={0}
            aria-valuemax={5}
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
    </div>
  );
});
