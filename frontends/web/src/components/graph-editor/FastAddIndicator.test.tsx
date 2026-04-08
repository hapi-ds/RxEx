/**
 * FastAddIndicator Tests
 * Validates that the indicator badge renders correctly based on fastAdd state.
 *
 * **Validates: Requirements 1.2**
 */

import React, { useEffect } from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GraphEditorProvider, useGraphEditor } from './GraphEditorContext';
import type { NodeType } from '../../types/generated';
import type { RelationshipType } from '../../types';
import { FastAddIndicator } from './FastAddIndicator';

function renderWithProvider(ui: React.ReactElement): ReturnType<typeof render> {
  return render(
    <GraphEditorProvider>{ui}</GraphEditorProvider>,
  );
}

/**
 * Helper component that enables fast-add mode and renders the indicator.
 */
function EnableAndRender({
  mindType,
  relType,
  direction = 'source',
}: {
  mindType?: NodeType;
  relType?: RelationshipType;
  direction?: 'source' | 'target';
}): React.ReactElement {
  const { dispatch } = useGraphEditor();

  useEffect(() => {
    dispatch({ type: 'SET_FAST_ADD_ENABLED', payload: true });
    if (mindType) {
      dispatch({ type: 'SET_FAST_ADD_MIND_TYPE', payload: mindType });
    }
    if (relType) {
      dispatch({ type: 'SET_FAST_ADD_RELATIONSHIP_TYPE', payload: relType });
    }
    dispatch({ type: 'SET_FAST_ADD_DIRECTION', payload: direction });
  }, [dispatch, mindType, relType, direction]);

  return <FastAddIndicator />;
}

describe('FastAddIndicator', () => {
  it('returns null when fastAdd.enabled is false', () => {
    const { container } = renderWithProvider(<FastAddIndicator />);
    expect(container.innerHTML).toBe('');
  });

  it('renders the indicator badge when fastAdd.enabled is true', () => {
    render(
      <GraphEditorProvider>
        <EnableAndRender />
      </GraphEditorProvider>,
    );

    expect(screen.getByTestId('fast-add-indicator')).toBeTruthy();
  });

  it('displays mind type and relationship type in the badge', () => {
    render(
      <GraphEditorProvider>
        <EnableAndRender mindType="risk" relType="LEAD_TO" />
      </GraphEditorProvider>,
    );

    const indicator = screen.getByTestId('fast-add-indicator');
    expect(indicator.textContent).toContain('risk');
    expect(indicator.textContent).toContain('LEAD_TO');
  });

  it('shows dash placeholders when types are not selected', () => {
    render(
      <GraphEditorProvider>
        <EnableAndRender />
      </GraphEditorProvider>,
    );

    const indicator = screen.getByTestId('fast-add-indicator');
    expect(indicator.textContent).toContain('—');
  });

  it('shows right arrow when direction is source', () => {
    render(
      <GraphEditorProvider>
        <EnableAndRender direction="source" />
      </GraphEditorProvider>,
    );

    const indicator = screen.getByTestId('fast-add-indicator');
    expect(indicator.textContent).toContain('→');
  });

  it('shows left arrow when direction is target', () => {
    render(
      <GraphEditorProvider>
        <EnableAndRender direction="target" />
      </GraphEditorProvider>,
    );

    const indicator = screen.getByTestId('fast-add-indicator');
    expect(indicator.textContent).toContain('←');
  });

  it('has proper role and aria-live attributes for accessibility', () => {
    render(
      <GraphEditorProvider>
        <EnableAndRender />
      </GraphEditorProvider>,
    );

    const indicator = screen.getByTestId('fast-add-indicator');
    expect(indicator.getAttribute('role')).toBe('status');
    expect(indicator.getAttribute('aria-live')).toBe('polite');
  });
});
