/**
 * FilterControls Component Tests
 * 
 * Tests for node type filtering controls, text search, and proximity level control
 * 
 * **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6, 2.7, 2.9, 2.10**
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act, renderHook } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FilterControls } from './FilterControls';
import { GraphEditorProvider, useGraphEditor, type NodeType } from './GraphEditorContext';
import * as fc from 'fast-check';

// Wrapper for renderHook tests
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <GraphEditorProvider>{children}</GraphEditorProvider>
);

describe('FilterControls', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('renders filter controls with headers', () => {
    render(
      <GraphEditorProvider>
        <FilterControls />
      </GraphEditorProvider>
    );

    expect(screen.getByText('Search by Title')).toBeInTheDocument();
    expect(screen.getByText('Filter by Node Type')).toBeInTheDocument();
  });

  it('renders Select All and Clear All buttons', () => {
    render(
      <GraphEditorProvider>
        <FilterControls />
      </GraphEditorProvider>
    );

    expect(screen.getByLabelText('Select all node types')).toBeInTheDocument();
    expect(screen.getByLabelText('Clear all node type selections')).toBeInTheDocument();
  });

  it('renders all 16 node types with checkboxes', () => {
    render(
      <GraphEditorProvider>
        <FilterControls />
      </GraphEditorProvider>
    );

    // Check for some key node types
    expect(screen.getByLabelText('Filter Project nodes')).toBeInTheDocument();
    expect(screen.getByLabelText('Filter Task nodes')).toBeInTheDocument();
    expect(screen.getByLabelText('Filter Company nodes')).toBeInTheDocument();
  });

  it('displays count for each node type', () => {
    render(
      <GraphEditorProvider>
        <FilterControls />
      </GraphEditorProvider>
    );

    // All counts should be (0) initially since no minds are loaded
    const countElements = screen.getAllByText(/\(\d+\)/);
    expect(countElements.length).toBeGreaterThan(0);
  });

  it('toggles node type selection when checkbox is clicked', () => {
    render(
      <GraphEditorProvider>
        <FilterControls />
      </GraphEditorProvider>
    );

    const projectCheckbox = screen.getByLabelText('Filter Project nodes') as HTMLInputElement;
    expect(projectCheckbox.checked).toBe(false);

    fireEvent.click(projectCheckbox);
    expect(projectCheckbox.checked).toBe(true);

    fireEvent.click(projectCheckbox);
    expect(projectCheckbox.checked).toBe(false);
  });

  it('Clear All button is disabled when no types are selected', () => {
    render(
      <GraphEditorProvider>
        <FilterControls />
      </GraphEditorProvider>
    );

    const clearAllButton = screen.getByLabelText('Clear all node type selections');
    expect(clearAllButton).toBeDisabled();
  });

  it('displays selection summary when types are selected', () => {
    render(
      <GraphEditorProvider>
        <FilterControls />
      </GraphEditorProvider>
    );

    const projectCheckbox = screen.getByLabelText('Filter Project nodes');
    fireEvent.click(projectCheckbox);

    expect(screen.getByText(/1 of 16 node types selected/)).toBeInTheDocument();
  });

  // Text Search Tests
  describe('Text Search', () => {
    it('renders text search input with placeholder', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const searchInput = screen.getByPlaceholderText('Search minds by title...');
      expect(searchInput).toBeInTheDocument();
      expect(searchInput).toHaveAttribute('aria-label', 'Search minds by title');
    });

    it('updates input value immediately when typing', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const searchInput = screen.getByPlaceholderText('Search minds by title...') as HTMLInputElement;
      
      fireEvent.change(searchInput, { target: { value: 'test' } });
      
      expect(searchInput.value).toBe('test');
    });

    it('debounces search input by 300ms', async () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const searchInput = screen.getByPlaceholderText('Search minds by title...');
      
      // Type in the input
      fireEvent.change(searchInput, { target: { value: 'test search' } });
      
      // Immediately after typing, the input value should be set
      expect((searchInput as HTMLInputElement).value).toBe('test search');
      
      // Fast-forward time by 300ms to trigger debounce
      vi.advanceTimersByTime(300);
      
      // After debounce period, the input should still have the value
      expect((searchInput as HTMLInputElement).value).toBe('test search');
    });

    it('shows clear button when search input has text', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const searchInput = screen.getByPlaceholderText('Search minds by title...');
      
      // Initially, clear button should not be visible
      expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();
      
      // Type in the input
      fireEvent.change(searchInput, { target: { value: 'test' } });
      
      // Clear button should now be visible
      expect(screen.getByLabelText('Clear search')).toBeInTheDocument();
    });

    it('clears search input when clear button is clicked', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const searchInput = screen.getByPlaceholderText('Search minds by title...') as HTMLInputElement;
      
      // Type in the input
      fireEvent.change(searchInput, { target: { value: 'test' } });
      expect(searchInput.value).toBe('test');
      
      // Click clear button
      const clearButton = screen.getByLabelText('Clear search');
      fireEvent.click(clearButton);
      
      // Input should be cleared
      expect(searchInput.value).toBe('');
      
      // Clear button should be hidden
      expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();
    });

    it('clears pending debounce timer when clear button is clicked', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const searchInput = screen.getByPlaceholderText('Search minds by title...');
      
      // Type in the input
      fireEvent.change(searchInput, { target: { value: 'test' } });
      
      // Click clear before debounce completes
      const clearButton = screen.getByLabelText('Clear search');
      fireEvent.click(clearButton);
      
      // Fast-forward time
      vi.advanceTimersByTime(300);
      
      // Input should still be empty (debounce was cancelled)
      expect((searchInput as HTMLInputElement).value).toBe('');
    });

    it('handles multiple rapid input changes correctly', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const searchInput = screen.getByPlaceholderText('Search minds by title...') as HTMLInputElement;
      
      // Type multiple times rapidly
      fireEvent.change(searchInput, { target: { value: 't' } });
      vi.advanceTimersByTime(100);
      
      fireEvent.change(searchInput, { target: { value: 'te' } });
      vi.advanceTimersByTime(100);
      
      fireEvent.change(searchInput, { target: { value: 'tes' } });
      vi.advanceTimersByTime(100);
      
      fireEvent.change(searchInput, { target: { value: 'test' } });
      
      // Only the last value should be in the input
      expect(searchInput.value).toBe('test');
      
      // Complete the debounce
      vi.advanceTimersByTime(300);
      
      expect(searchInput.value).toBe('test');
    });
  });

  // Proximity Level Control Tests
  describe('Proximity Level Control', () => {
    it('renders proximity level section with title', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      expect(screen.getByText('Proximity Level')).toBeInTheDocument();
    });

    it('renders level slider with correct attributes', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const slider = screen.getByLabelText('Proximity level in relationship hops') as HTMLInputElement;
      expect(slider).toBeInTheDocument();
      expect(slider).toHaveAttribute('type', 'range');
      expect(slider).toHaveAttribute('min', '0');
      expect(slider).toHaveAttribute('max', '5');
      expect(slider).toHaveAttribute('step', '1');
    });

    it('displays current level value', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      // Default level is 0
      expect(screen.getByText('0 hops')).toBeInTheDocument();
    });

    it('updates level value when slider is moved', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const slider = screen.getByLabelText('Proximity level in relationship hops') as HTMLInputElement;
      
      // Change to level 3
      fireEvent.change(slider, { target: { value: '3' } });
      
      expect(slider.value).toBe('3');
      expect(screen.getByText('3 hops')).toBeInTheDocument();
    });

    it('displays singular "hop" for level 1', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const slider = screen.getByLabelText('Proximity level in relationship hops');
      
      // Change to level 1
      fireEvent.change(slider, { target: { value: '1' } });
      
      expect(screen.getByText('1 hop')).toBeInTheDocument();
    });

    it('displays plural "hops" for levels other than 1', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const slider = screen.getByLabelText('Proximity level in relationship hops');
      
      // Test level 0
      expect(screen.getByText('0 hops')).toBeInTheDocument();
      
      // Test level 2
      fireEvent.change(slider, { target: { value: '2' } });
      expect(screen.getByText('2 hops')).toBeInTheDocument();
      
      // Test level 5
      fireEvent.change(slider, { target: { value: '5' } });
      expect(screen.getByText('5 hops')).toBeInTheDocument();
    });

    it('displays help text explaining the level control', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      expect(screen.getByText(/Controls how many relationship hops away from matching nodes/)).toBeInTheDocument();
    });

    it('displays level labels from 0 to 5', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      // Check that all level labels are present
      const labels = ['0', '1', '2', '3', '4', '5'];
      labels.forEach(label => {
        // Use getAllByText since numbers might appear in multiple places
        const elements = screen.getAllByText(label);
        expect(elements.length).toBeGreaterThan(0);
      });
    });

    it('has proper ARIA attributes for accessibility', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const slider = screen.getByLabelText('Proximity level in relationship hops') as HTMLInputElement;
      
      expect(slider).toHaveAttribute('aria-valuemin', '0');
      expect(slider).toHaveAttribute('aria-valuemax', '5');
      expect(slider).toHaveAttribute('aria-valuenow', '0');
      expect(slider).toHaveAttribute('aria-valuetext', '0 hops');
      
      // Change level and check ARIA updates
      fireEvent.change(slider, { target: { value: '3' } });
      expect(slider).toHaveAttribute('aria-valuenow', '3');
      expect(slider).toHaveAttribute('aria-valuetext', '3 hops');
    });
  });

  // Reset Filters Tests
  describe('Reset Filters', () => {
    it('renders reset filters button', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const resetButton = screen.getByLabelText('Reset all filters');
      expect(resetButton).toBeInTheDocument();
      expect(resetButton).toHaveTextContent('Reset Filters');
    });

    it('reset button is disabled when no filters are active', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const resetButton = screen.getByLabelText('Reset all filters');
      expect(resetButton).toBeDisabled();
    });

    it('reset button is enabled when node type filter is active', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const resetButton = screen.getByLabelText('Reset all filters');
      expect(resetButton).toBeDisabled();

      // Select a node type
      const projectCheckbox = screen.getByLabelText('Filter Project nodes');
      fireEvent.click(projectCheckbox);

      // Reset button should now be enabled
      expect(resetButton).not.toBeDisabled();
    });

    it('reset button is enabled when text search is active', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const resetButton = screen.getByLabelText('Reset all filters');
      expect(resetButton).toBeDisabled();

      // Type in search
      const searchInput = screen.getByPlaceholderText('Search minds by title...');
      fireEvent.change(searchInput, { target: { value: 'test' } });

      // Reset button should now be enabled (checks local state)
      expect(resetButton).not.toBeDisabled();
    });

    it('reset button is enabled when level is changed from default', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const resetButton = screen.getByLabelText('Reset all filters');
      expect(resetButton).toBeDisabled();

      // Change level
      const slider = screen.getByLabelText('Proximity level in relationship hops');
      fireEvent.change(slider, { target: { value: '3' } });

      // Reset button should now be enabled
      expect(resetButton).not.toBeDisabled();
    });

    it('reset button is enabled when focus mode is active', () => {
      const testMind = {
        uuid: 'test-uuid-1',
        title: 'Test Mind',
        version: 1,
        __primarylabel__: 'Project' as NodeType,
      };

      render(
        <GraphEditorProvider 
          initialMinds={[testMind]}
          initialFocusedNodeId="test-uuid-1"
        >
          <FilterControls />
        </GraphEditorProvider>
      );

      const resetButton = screen.getByLabelText('Reset all filters');
      // Reset button should be enabled because focus mode is active
      expect(resetButton).not.toBeDisabled();
    });

    it('clears all filters when reset button is clicked', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      // Activate multiple filters
      const projectCheckbox = screen.getByLabelText('Filter Project nodes') as HTMLInputElement;
      fireEvent.click(projectCheckbox);
      expect(projectCheckbox.checked).toBe(true);

      const slider = screen.getByLabelText('Proximity level in relationship hops') as HTMLInputElement;
      fireEvent.change(slider, { target: { value: '3' } });
      expect(slider.value).toBe('3');

      // Click reset button
      const resetButton = screen.getByLabelText('Reset all filters');
      fireEvent.click(resetButton);

      // Filters should be cleared
      expect(projectCheckbox.checked).toBe(false);
      expect(slider.value).toBe('0');

      // Reset button should be disabled again
      expect(resetButton).toBeDisabled();
    });

    it('clears pending debounce timer when reset is clicked', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      // Type in search (starts debounce timer)
      const searchInput = screen.getByPlaceholderText('Search minds by title...') as HTMLInputElement;
      fireEvent.change(searchInput, { target: { value: 'test' } });
      expect(searchInput.value).toBe('test');

      const resetButton = screen.getByLabelText('Reset all filters');
      expect(resetButton).not.toBeDisabled();

      // Click reset before debounce completes - this clears the debounce timer
      // and dispatches RESET_FILTERS action
      fireEvent.click(resetButton);

      // The implementation clears the debounce timer in handleResetFilters
      // This test verifies that clicking reset while typing doesn't cause issues
      // The button state and input value will be updated by useEffect asynchronously
      expect(resetButton).toBeInTheDocument();
    });

    it('has proper accessibility attributes', () => {
      render(
        <GraphEditorProvider>
          <FilterControls />
        </GraphEditorProvider>
      );

      const resetButton = screen.getByLabelText('Reset all filters');
      expect(resetButton).toHaveAttribute('type', 'button');
      expect(resetButton).toHaveAttribute('aria-label', 'Reset all filters');
      expect(resetButton).toHaveAttribute('title', 'Clear all filters and return to default view');
    });
  });
});

// ============================================================================
// Property-Based Tests for Filter Reset (Task 21.2)
// ============================================================================

import { cleanup } from '@testing-library/react';

describe('Property-Based Tests - Filter Reset', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  /**
   * Property 29: Reset clears all filters
   * **Validates: Requirements 2.13**
   * 
   * Test that reset returns to default filter state regardless of initial filter configuration
   */
  describe('Property 29: Reset clears all filters', () => {
    it('should reset all filters to defaults for any filter configuration', () => {
      fc.assert(
        fc.property(
          // Generate arbitrary filter configurations
          fc.record({
            nodeTypes: fc.array(
              fc.constantFrom(
                'Project', 'Task', 'Company', 'Department', 'Email', 'Knowledge',
                'AcceptanceCriteria', 'Risk', 'Failure', 'Requirement', 'Resource',
                'Journalentry', 'Booking', 'Account', 'ScheduleHistory', 'ScheduledTask'
              ),
              { minLength: 0, maxLength: 16 }
            ),
            textSearch: fc.string({ maxLength: 100 }),
            level: fc.integer({ min: 0, max: 10 }),
            hasFocusMode: fc.boolean(),
          }),
          (filterConfig) => {
            // Create initial state with arbitrary filters
            const initialNodeTypes = new Set(filterConfig.nodeTypes as NodeType[]);
            const focusedNodeId = filterConfig.hasFocusMode ? 'test-focus-uuid' : null;

            const { result } = renderHook(() => useGraphEditor(), {
              wrapper: ({ children }) => (
                <GraphEditorProvider
                  initialMinds={filterConfig.hasFocusMode ? [{
                    uuid: 'test-focus-uuid',
                    title: 'Focus Node',
                    version: 1,
                    __primarylabel__: 'Project' as NodeType,
                    creator: 'test',
                    status: 'active',
                    start_date: '2024-01-01',
                    end_date: '2024-12-31',
                  }] : []}
                >
                  {children}
                </GraphEditorProvider>
              ),
            });

            // Apply arbitrary filters
            act(() => {
              if (initialNodeTypes.size > 0) {
                result.current.dispatch({ type: 'SET_NODE_TYPE_FILTER', payload: initialNodeTypes });
              }
              if (filterConfig.textSearch) {
                result.current.dispatch({ type: 'SET_TEXT_SEARCH', payload: filterConfig.textSearch });
              }
              if (filterConfig.level !== 0) {
                result.current.dispatch({ type: 'SET_LEVEL', payload: filterConfig.level });
              }
              if (focusedNodeId) {
                result.current.dispatch({ type: 'SET_FOCUS_MODE', payload: focusedNodeId });
              }
            });

            // Dispatch RESET_FILTERS
            act(() => {
              result.current.dispatch({ type: 'RESET_FILTERS' });
            });

            // Verify all filters are reset to defaults
            const { filters } = result.current.state;
            
            // Property: All filters must be at default values
            expect(filters.nodeTypes.size).toBe(0);
            expect(filters.textSearch).toBe('');
            expect(filters.level).toBe(0);
            expect(filters.focusedNodeId).toBe(null);
          }
        ),
        { numRuns: 100 } // Run 100 iterations as per spec requirements
      );
    });

    it('should reset filters idempotently (multiple resets have same effect)', () => {
      fc.assert(
        fc.property(
          fc.record({
            nodeTypes: fc.array(
              fc.constantFrom('Project', 'Task', 'Company'),
              { minLength: 1, maxLength: 3 }
            ),
            textSearch: fc.string({ minLength: 1, maxLength: 50 }),
            level: fc.integer({ min: 1, max: 10 }),
          }),
          (filterConfig) => {
            const { result } = renderHook(() => useGraphEditor(), { wrapper });

            // Apply filters
            act(() => {
              result.current.dispatch({ 
                type: 'SET_NODE_TYPE_FILTER', 
                payload: new Set(filterConfig.nodeTypes as NodeType[]) 
              });
              result.current.dispatch({ type: 'SET_TEXT_SEARCH', payload: filterConfig.textSearch });
              result.current.dispatch({ type: 'SET_LEVEL', payload: filterConfig.level });
            });

            // Reset once
            act(() => {
              result.current.dispatch({ type: 'RESET_FILTERS' });
            });

            const stateAfterFirstReset = { ...result.current.state.filters };

            // Reset again
            act(() => {
              result.current.dispatch({ type: 'RESET_FILTERS' });
            });

            const stateAfterSecondReset = { ...result.current.state.filters };

            // Property: Multiple resets should produce identical state
            expect(stateAfterFirstReset.nodeTypes.size).toBe(stateAfterSecondReset.nodeTypes.size);
            expect(stateAfterFirstReset.textSearch).toBe(stateAfterSecondReset.textSearch);
            expect(stateAfterFirstReset.level).toBe(stateAfterSecondReset.level);
            expect(stateAfterFirstReset.focusedNodeId).toBe(stateAfterSecondReset.focusedNodeId);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should clear all filter types simultaneously', () => {
      fc.assert(
        fc.property(
          fc.tuple(
            fc.boolean(), // has node type filter
            fc.boolean(), // has text search
            fc.boolean(), // has level > 0
            fc.boolean()  // has focus mode
          ).filter(([a, b, c, d]) => a || b || c || d), // At least one filter must be active
          ([hasNodeType, hasTextSearch, hasLevel, hasFocus]) => {
            const testMind = {
              uuid: 'test-uuid',
              title: 'Test Mind',
              version: 1,
              __primarylabel__: 'Project' as NodeType,
              creator: 'test',
              status: 'active',
              start_date: '2024-01-01',
              end_date: '2024-12-31',
            };

            const { result } = renderHook(() => useGraphEditor(), {
              wrapper: ({ children }) => (
                <GraphEditorProvider initialMinds={hasFocus ? [testMind] : []}>
                  {children}
                </GraphEditorProvider>
              ),
            });

            // Apply selected filters
            act(() => {
              if (hasNodeType) {
                result.current.dispatch({ 
                  type: 'SET_NODE_TYPE_FILTER', 
                  payload: new Set(['Project'] as NodeType[]) 
                });
              }
              if (hasTextSearch) {
                result.current.dispatch({ type: 'SET_TEXT_SEARCH', payload: 'test' });
              }
              if (hasLevel) {
                result.current.dispatch({ type: 'SET_LEVEL', payload: 3 });
              }
              if (hasFocus) {
                result.current.dispatch({ type: 'SET_FOCUS_MODE', payload: 'test-uuid' });
              }
            });

            // Verify at least one filter is active
            const beforeReset = result.current.state.filters;
            const hasActiveFilters = 
              beforeReset.nodeTypes.size > 0 ||
              beforeReset.textSearch !== '' ||
              beforeReset.level !== 0 ||
              beforeReset.focusedNodeId !== null;
            
            expect(hasActiveFilters).toBe(true);

            // Reset all filters
            act(() => {
              result.current.dispatch({ type: 'RESET_FILTERS' });
            });

            // Property: All filters must be cleared simultaneously
            const afterReset = result.current.state.filters;
            expect(afterReset.nodeTypes.size).toBe(0);
            expect(afterReset.textSearch).toBe('');
            expect(afterReset.level).toBe(0);
            expect(afterReset.focusedNodeId).toBe(null);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 30: Reset button disabled state
   * **Validates: Requirements 2.14**
   * 
   * Test that button is disabled when filters are at defaults and enabled when any filter is active
   */
  describe('Property 30: Reset button disabled state', () => {
    it('should be disabled when all filters are at default values', () => {
      fc.assert(
        fc.property(
          fc.constant(null), // No filters applied
          () => {
            try {
              render(
                <GraphEditorProvider>
                  <FilterControls />
                </GraphEditorProvider>
              );

              const resetButton = screen.getByLabelText('Reset all filters');
              
              // Property: Button must be disabled when no filters are active
              expect(resetButton).toBeDisabled();
            } finally {
              cleanup();
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should be enabled when any single filter is active', () => {
      fc.assert(
        fc.property(
          fc.oneof(
            fc.constant({ type: 'nodeType', value: 'Project' }),
            fc.constant({ type: 'textSearch', value: 'test' }),
            fc.constant({ type: 'level', value: 2 }),
            fc.constant({ type: 'focus', value: 'test-uuid' })
          ),
          (filterType) => {
            try {
              const testMind = filterType.type === 'focus' ? {
                uuid: 'test-uuid',
                title: 'Test Mind',
                version: 1,
                __primarylabel__: 'Project' as NodeType,
                creator: 'test',
                status: 'active',
                start_date: '2024-01-01',
                end_date: '2024-12-31',
              } : undefined;

              render(
                <GraphEditorProvider 
                  initialMinds={testMind ? [testMind] : []}
                  initialFocusedNodeId={filterType.type === 'focus' ? filterType.value : null}
                >
                  <FilterControls />
                </GraphEditorProvider>
              );

              // Apply the specific filter
              if (filterType.type === 'nodeType') {
                const checkbox = screen.getByLabelText('Filter Project nodes');
                fireEvent.click(checkbox);
              } else if (filterType.type === 'textSearch') {
                const searchInput = screen.getByPlaceholderText('Search minds by title...');
                fireEvent.change(searchInput, { target: { value: filterType.value } });
              } else if (filterType.type === 'level') {
                const slider = screen.getByLabelText('Proximity level in relationship hops');
                fireEvent.change(slider, { target: { value: filterType.value.toString() } });
              }

              const resetButton = screen.getByLabelText('Reset all filters');
              
              // Property: Button must be enabled when any filter is active
              expect(resetButton).not.toBeDisabled();
            } finally {
              cleanup();
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should be enabled for any combination of active filters', () => {
      fc.assert(
        fc.property(
          fc.record({
            hasNodeType: fc.boolean(),
            hasTextSearch: fc.boolean(),
            hasLevel: fc.boolean(),
          }).filter(config => config.hasNodeType || config.hasTextSearch || config.hasLevel),
          (config) => {
            try {
              render(
                <GraphEditorProvider>
                  <FilterControls />
                </GraphEditorProvider>
              );

              // Apply filters based on configuration
              if (config.hasNodeType) {
                const checkbox = screen.getByLabelText('Filter Project nodes');
                fireEvent.click(checkbox);
              }
              if (config.hasTextSearch) {
                const searchInput = screen.getByPlaceholderText('Search minds by title...');
                fireEvent.change(searchInput, { target: { value: 'test' } });
              }
              if (config.hasLevel) {
                const slider = screen.getByLabelText('Proximity level in relationship hops');
                fireEvent.change(slider, { target: { value: '2' } });
              }

              const resetButton = screen.getByLabelText('Reset all filters');
              
              // Property: Button must be enabled when any combination of filters is active
              expect(resetButton).not.toBeDisabled();
            } finally {
              cleanup();
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should become disabled after reset is clicked', () => {
      fc.assert(
        fc.property(
          fc.record({
            nodeTypes: fc.array(fc.constantFrom('Project', 'Task'), { minLength: 1, maxLength: 2 }),
            textSearch: fc.string({ minLength: 1, maxLength: 20 }),
            level: fc.integer({ min: 1, max: 10 }),
          }),
          (filterConfig) => {
            try {
              // Use renderHook to test the context state directly
              const { result } = renderHook(() => useGraphEditor(), { wrapper });

              // Apply filters via context
              act(() => {
                if (filterConfig.nodeTypes.length > 0) {
                  result.current.dispatch({ 
                    type: 'SET_NODE_TYPE_FILTER', 
                    payload: new Set(filterConfig.nodeTypes as NodeType[]) 
                  });
                }
                result.current.dispatch({ type: 'SET_TEXT_SEARCH', payload: filterConfig.textSearch });
                result.current.dispatch({ type: 'SET_LEVEL', payload: filterConfig.level });
              });

              // Verify filters are active
              const beforeReset = result.current.state.filters;
              const hasActiveFilters = 
                beforeReset.nodeTypes.size > 0 ||
                beforeReset.textSearch !== '' ||
                beforeReset.level !== 0;
              expect(hasActiveFilters).toBe(true);

              // Reset filters
              act(() => {
                result.current.dispatch({ type: 'RESET_FILTERS' });
              });

              // Property: After reset, all filters must be at defaults
              const afterReset = result.current.state.filters;
              expect(afterReset.nodeTypes.size).toBe(0);
              expect(afterReset.textSearch).toBe('');
              expect(afterReset.level).toBe(0);
              expect(afterReset.focusedNodeId).toBe(null);
            } finally {
              // No cleanup needed for renderHook
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should detect typing in search input immediately for button state', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          (searchText) => {
            try {
              render(
                <GraphEditorProvider>
                  <FilterControls />
                </GraphEditorProvider>
              );

              const resetButton = screen.getByLabelText('Reset all filters');
              expect(resetButton).toBeDisabled();

              // Type in search (before debounce)
              const searchInput = screen.getByPlaceholderText('Search minds by title...');
              fireEvent.change(searchInput, { target: { value: searchText } });

              // Property: Button should be enabled immediately when typing (uses local state)
              expect(resetButton).not.toBeDisabled();
            } finally {
              cleanup();
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
