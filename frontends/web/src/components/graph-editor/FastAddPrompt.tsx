/**
 * FastAddPrompt Component
 * A small floating form that appears near a right-clicked node.
 * Collects the title field before creating a new mind via fast-add.
 * Creator is automatically set to the logged-in user.
 *
 * **Validates: Requirements 4.7**
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import './FastAddPrompt.css';

export interface FastAddPromptProps {
  position: { x: number; y: number };
  onSubmit: (data: { title: string }) => void;
  onCancel: () => void;
}

export function FastAddPrompt({ position, onSubmit, onCancel }: FastAddPromptProps): JSX.Element {
  const [title, setTitle] = useState('');
  const titleInputRef = useRef<HTMLInputElement>(null);

  // Auto-focus the title input on open
  useEffect(() => {
    titleInputRef.current?.focus();
  }, []);

  // Handle Escape key to cancel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onCancel]);

  const isValid = title.trim().length > 0;

  const handleSubmit = useCallback(
    (e: FormEvent): void => {
      e.preventDefault();
      if (!isValid) return;
      onSubmit({ title: title.trim() });
    },
    [isValid, title, onSubmit],
  );

  return (
    <>
      {/* Transparent backdrop to catch outside clicks */}
      <div
        className="fast-add-prompt-backdrop"
        onClick={onCancel}
        data-testid="fast-add-prompt-backdrop"
      />

      <div
        className="fast-add-prompt"
        style={{ left: position.x, top: position.y }}
        role="dialog"
        aria-label="Fast add new mind"
        data-testid="fast-add-prompt"
      >
        <div className="fast-add-prompt-header">
          <h3 className="fast-add-prompt-title">Quick Add Mind</h3>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="fast-add-prompt-body">
            <div className="fast-add-prompt-field">
              <label htmlFor="fast-add-title">Title *</label>
              <input
                id="fast-add-title"
                ref={titleInputRef}
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter title"
                required
                data-testid="fast-add-title-input"
              />
            </div>


          </div>

          <div className="fast-add-prompt-footer">
            <button
              type="button"
              className="fast-add-prompt-btn-cancel"
              onClick={onCancel}
              data-testid="fast-add-cancel-btn"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="fast-add-prompt-btn-submit"
              disabled={!isValid}
              data-testid="fast-add-submit-btn"
            >
              Submit
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
