/**
 * FastAddIndicator Component
 * A small floating badge on the canvas showing the active Fast Add Mode configuration.
 * Displays "Fast Add Mode: [MindType] → [RelType]" when fastAdd.enabled is true.
 *
 * **Validates: Requirements 1.2**
 */

import { useGraphEditor } from './GraphEditorContext';
import './FastAddIndicator.css';

export function FastAddIndicator(): JSX.Element | null {
  const { state } = useGraphEditor();
  const { fastAdd } = state;

  if (!fastAdd.enabled) {
    return null;
  }

  const mindTypeLabel = fastAdd.selectedMindType ?? '—';
  const relTypeLabel = fastAdd.selectedRelationshipType ?? '—';
  const directionArrow = fastAdd.relationDirection === 'source' ? '→' : '←';

  return (
    <div
      className="fast-add-indicator"
      role="status"
      aria-live="polite"
      data-testid="fast-add-indicator"
    >
      <span className="fast-add-indicator-dot" aria-hidden="true" />
      <span className="fast-add-indicator-text">
        Fast Add Mode: {mindTypeLabel} {directionArrow} {relTypeLabel}
      </span>
    </div>
  );
}
