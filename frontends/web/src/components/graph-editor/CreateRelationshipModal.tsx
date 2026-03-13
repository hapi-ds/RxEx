/**
 * CreateRelationshipModal Component
 * Modal for creating new relationships between nodes
 * 
 * Features:
 * - Select source node
 * - Select target node
 * - Select relationship type
 * - Validate selections
 * - Create relationship via API
 * - Add new edge to graph state
 * 
 * **Validates: Requirements 5.2, 5.4**
 */

import { useState, useEffect } from 'react';
import { useGraphEditor } from './GraphEditorContext';
import { relationshipsAPI } from '../../services/api';
import { useToast } from './ToastContext';
import { useScreenReaderAnnouncer } from './ScreenReaderAnnouncer';
import type { RelationshipType } from '../../types';
import { mindTypeToNodeType } from '../../utils/mindTypeUtils';
import './CreateRelationshipModal.css';

export interface CreateRelationshipModalProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * CreateRelationshipModal Component
 * Modal for creating relationships between nodes
 */
export function CreateRelationshipModal({ isOpen, onClose }: CreateRelationshipModalProps) {
  const { state, dispatch } = useGraphEditor();
  const { showToast } = useToast();
  const { announceCRUDOperation } = useScreenReaderAnnouncer();
  
  const [sourceNodeId, setSourceNodeId] = useState<string>('');
  const [targetNodeId, setTargetNodeId] = useState<string>('');
  const [relationshipType, setRelationshipType] = useState<RelationshipType>('CONTAINS');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string>('');

  // Get list of available nodes
  const availableNodes = Array.from(state.minds.values());

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setSourceNodeId('');
      setTargetNodeId('');
      setRelationshipType('CONTAINS');
      setValidationError('');
    }
  }, [isOpen]);

  // Validate selections
  const validateSelections = (): boolean => {
    if (!sourceNodeId) {
      setValidationError('Please select a source node');
      return false;
    }
    if (!targetNodeId) {
      setValidationError('Please select a target node');
      return false;
    }
    if (sourceNodeId === targetNodeId) {
      setValidationError('Source and target nodes must be different');
      return false;
    }
    setValidationError('');
    return true;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate selections
    if (!validateSelections()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Create relationship via API
      const newRelationship = await relationshipsAPI.create({
        type: relationshipType,
        source: sourceNodeId,
        target: targetNodeId,
        properties: {},
      });

      // Add new relationship to graph state
      dispatch({ type: 'ADD_RELATIONSHIP', payload: newRelationship });

      // Show success notification
      showToast('success', 'Relationship created successfully');

      // Announce CRUD operation
      announceCRUDOperation('created', 'relationship');

      // Close modal
      onClose();
    } catch (error) {
      // Handle error
      const errorMessage = error instanceof Error ? error.message : 'Failed to create relationship';
      setValidationError(errorMessage);
      showToast('error', errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="modal-overlay" 
      onClick={handleCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-relationship-title"
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 id="create-relationship-title">Create Relationship</h2>
          <button
            className="modal-close-button"
            onClick={handleCancel}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="create-relationship-form">
          {/* Source Node Selection */}
          <div className="form-group">
            <label htmlFor="source-node">
              Source Node <span className="required" aria-label="required">*</span>
            </label>
            <select
              id="source-node"
              value={sourceNodeId}
              onChange={(e) => setSourceNodeId(e.target.value)}
              className="form-select"
              required
              aria-required="true"
              aria-label="Select source node for relationship"
            >
              <option value="">Select source node...</option>
              {availableNodes.map((node) => (
                <option key={node.uuid} value={node.uuid}>
                  {node.title} ({mindTypeToNodeType((node as any).mind_type)})
                </option>
              ))}
            </select>
          </div>

          {/* Target Node Selection */}
          <div className="form-group">
            <label htmlFor="target-node">
              Target Node <span className="required" aria-label="required">*</span>
            </label>
            <select
              id="target-node"
              value={targetNodeId}
              onChange={(e) => setTargetNodeId(e.target.value)}
              className="form-select"
              required
              aria-required="true"
              aria-label="Select target node for relationship"
            >
              <option value="">Select target node...</option>
              {availableNodes.map((node) => (
                <option key={node.uuid} value={node.uuid}>
                  {node.title} ({mindTypeToNodeType((node as any).mind_type)})
                </option>
              ))}
            </select>
          </div>

          {/* Relationship Type Selection */}
          <div className="form-group">
            <label htmlFor="relationship-type">
              Relationship Type <span className="required" aria-label="required">*</span>
            </label>
            <select
              id="relationship-type"
              value={relationshipType}
              onChange={(e) => setRelationshipType(e.target.value as RelationshipType)}
              className="form-select"
              required
              aria-required="true"
              aria-label="Select relationship type"
            >
              <option value="PREVIOUS">PREVIOUS</option>
              <option value="SCHEDULED">SCHEDULED</option>
              <option value="CONTAINS">CONTAINS</option>
              <option value="PREDATES">PREDATES</option>
              <option value="ASSIGNED_TO">ASSIGNED_TO</option>
              <option value="TO">TO</option>
              <option value="FOR">FOR</option>
              <option value="REFINES">REFINES</option>
            </select>
          </div>

          {/* Validation Error */}
          {validationError && (
            <div className="validation-error" role="alert">
              {validationError}
            </div>
          )}

          {/* Form Actions */}
          <div className="form-actions" role="group" aria-label="Form actions">
            <button
              type="button"
              onClick={handleCancel}
              className="button-secondary"
              disabled={isSubmitting}
              aria-label="Cancel relationship creation"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="button-primary"
              disabled={isSubmitting}
              aria-label="Create relationship"
            >
              {isSubmitting ? 'Creating...' : 'Create Relationship'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
