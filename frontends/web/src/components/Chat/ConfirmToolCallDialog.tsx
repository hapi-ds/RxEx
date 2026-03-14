/**
 * ConfirmToolCallDialog Component
 * Editable confirmation dialog for AI-suggested graph modifications
 */

import { useEffect, useState } from 'react';
import type { ToolCall } from '../../types/chat';
import './ConfirmToolCallDialog.css';

export interface ConfirmToolCallDialogProps {
  toolCall: ToolCall;
  totalCount: number;
  currentIndex: number;
  onConfirm: (editedToolCall: ToolCall) => void;
  onCancel: () => void;
  onConfirmAll?: () => void;
  onCancelAll?: () => void;
}

const LABEL_MAP: Record<string, string> = {
  mind_type: 'Type',
  title: 'Title',
  description: 'Description',
  status: 'Status',
  source_uuid: 'Source UUID',
  target_uuid: 'Target UUID',
  relationship_type: 'Relationship Type',
};

const formatToolName = (name: string): string =>
  name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

export function ConfirmToolCallDialog({
  toolCall,
  totalCount,
  currentIndex,
  onConfirm,
  onCancel,
  onConfirmAll,
  onCancelAll,
}: ConfirmToolCallDialogProps) {
  const [editedArgs, setEditedArgs] = useState<Record<string, unknown>>(
    () => ({ ...toolCall.arguments })
  );

  // Reset edited args when toolCall changes (advancing through queue)
  useEffect(() => {
    setEditedArgs({ ...toolCall.arguments });
  }, [toolCall]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [onCancel]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onCancel();
  };

  const handleFieldChange = (key: string, value: string) => {
    setEditedArgs(prev => ({ ...prev, [key]: value }));
  };

  const handleConfirm = () => {
    onConfirm({ tool_name: toolCall.tool_name, arguments: editedArgs });
  };

  const isMultiline = (value: unknown): boolean =>
    typeof value === 'string' && value.length > 60;

  return (
    <div
      className="confirm-tool-call-backdrop"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-tool-call-title"
    >
      <div className="confirm-tool-call-content">
        <div className="confirm-tool-call-header">
          <h2 id="confirm-tool-call-title" className="confirm-tool-call-title">
            Confirm AI Suggestion
          </h2>
          {totalCount > 1 && (
            <span className="batch-indicator">
              {currentIndex + 1} of {totalCount} actions
            </span>
          )}
        </div>

        <div className="confirm-tool-call-body">
          <p className="confirm-tool-call-description">
            Review and edit the suggested action before confirming:
          </p>

          <div className="tool-call-details">
            <div className="tool-call-name">
              <strong>Action:</strong> {formatToolName(toolCall.tool_name)}
            </div>

            <div className="tool-call-arguments">
              <strong>Details:</strong>
              <dl className="arguments-list">
                {Object.entries(editedArgs).map(([key, value]) => (
                  <div key={key} className="argument-item">
                    <dt className="argument-key">
                      {LABEL_MAP[key] || key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}:
                    </dt>
                    <dd className="argument-value">
                      {isMultiline(value) ? (
                        <textarea
                          className="argument-input argument-textarea"
                          value={String(value ?? '')}
                          onChange={e => handleFieldChange(key, e.target.value)}
                          rows={3}
                        />
                      ) : (
                        <input
                          className="argument-input"
                          type="text"
                          value={String(value ?? '')}
                          onChange={e => handleFieldChange(key, e.target.value)}
                        />
                      )}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </div>

        <div className="confirm-tool-call-footer">
          {onCancelAll && (
            <button className="btn btn-secondary" onClick={onCancelAll}>
              Cancel All
            </button>
          )}
          <button className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleConfirm} autoFocus>
            Confirm
          </button>
          {onConfirmAll && (
            <button className="btn btn-primary" onClick={onConfirmAll}>
              Confirm All ({totalCount})
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
