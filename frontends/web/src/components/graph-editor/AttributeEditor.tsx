/**
 * AttributeEditor Component
 * Displays and enables editing of node/relationship attributes
 * 
 * Features:
 * - Displays all attributes of selected node or relationship
 * - Read-only fields: uuid, version, created_at, updated_at
 * - Editable fields based on node type configuration
 * - Type-appropriate input controls (text, number, date, select, array)
 * - Inline validation with error messages
 * - Save/Cancel/Delete actions
 * 
 * **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 4.6**
 */

import { useState, useEffect } from 'react';
import { useGraphEditor } from './GraphEditorContext';
import { useToast } from './ToastContext';
import { useScreenReaderAnnouncer } from './ScreenReaderAnnouncer';
import { Spinner } from './LoadingSkeleton';
import type { Mind } from '../../types/generated';
import { getNodeTypeConfig } from './nodeTypeConfig';
import type { AttributeConfig } from './nodeTypeConfig';
import { TextInput, NumberInput, DateInput, EnumInput, ArrayInput } from './form-inputs';
import { mindsAPI, relationshipsAPI } from '../../services/api';
import { ConfirmDialog } from './ConfirmDialog';
import { mindTypeToNodeType } from '../../utils/mindTypeUtils';
import './AttributeEditor.css';

/**
 * AttributeEditor Component
 * Displays attributes of the selected node or relationship
 */
export function AttributeEditor() {
  const { state } = useGraphEditor();
  const { selection, minds, relationships } = state;

  // Determine what to display based on selection
  const selectedNode = selection.selectedNodeId 
    ? minds.get(selection.selectedNodeId) 
    : null;
  
  const selectedEdge = selection.selectedEdgeId 
    ? relationships.get(selection.selectedEdgeId) 
    : null;

  // Priority: Show edge if selected, otherwise show node
  if (selectedEdge) {
    return <RelationshipAttributeView relationship={selectedEdge} />;
  }

  if (selectedNode) {
    return <NodeAttributeView node={selectedNode} />;
  }

  // No selection - show prompt
  return (
    <div className="attribute-editor" role="region" aria-label="Attribute Editor">
      <div className="attribute-editor-empty">
        <p>Select a node or relationship to view its attributes</p>
      </div>
    </div>
  );
}

/**
 * NodeAttributeView Component
 * Displays all attributes of a selected node with dynamic form rendering
 */
function NodeAttributeView({ node }: { node: Mind }) {
  const { dispatch } = useGraphEditor();
  const { showSuccess, showError } = useToast();
  const { announceCRUDOperation } = useScreenReaderAnnouncer();
  const [formData, setFormData] = useState<Mind>(node);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Map<string, string>>(new Map());

  // Get config, fallback to a default if not found
  const nodeType = mindTypeToNodeType((node as any).mind_type);
  const config = getNodeTypeConfig(nodeType);

  // Sync formData with node prop when it changes (e.g., after successful save or node selection change)
  useEffect(() => {
    setFormData(node);
    setIsDirty(false);
    setValidationErrors(new Map());
  }, [node]);

  const handleFieldChange = (fieldName: string, value: unknown) => {
    setFormData(prev => ({ ...prev, [fieldName]: value } as Mind));
    setIsDirty(true);
    // Clear validation error for this field when user makes changes
    if (validationErrors.has(fieldName)) {
      const newErrors = new Map(validationErrors);
      newErrors.delete(fieldName);
      setValidationErrors(newErrors);
    }
  };

  /**
   * Validate all fields before save
   * **Validates: Requirements 5.4, 5.5**
   */
  const validateAllFields = (): boolean => {
    const errors = new Map<string, string>();
    
    config.attributes
      .filter(attr => !attr.readonly)
      .forEach(attr => {
        const value = (formData as unknown as Record<string, unknown>)[attr.name];
        
        // Required field validation
        if (attr.required && (value === null || value === undefined || value === '')) {
          errors.set(attr.name, `${attr.label} is required`);
          return;
        }
        
        // Skip further validation if field is empty and not required
        if (!attr.required && (value === null || value === undefined || value === '')) {
          return;
        }
        
        // Type-specific validation
        if (attr.type === 'string' && typeof value === 'string') {
          if (attr.validation?.minLength && value.length < attr.validation.minLength) {
            errors.set(attr.name, `${attr.label} must be at least ${attr.validation.minLength} characters`);
          }
          if (attr.validation?.maxLength && value.length > attr.validation.maxLength) {
            errors.set(attr.name, `${attr.label} must be at most ${attr.validation.maxLength} characters`);
          }
          if (attr.validation?.pattern && !new RegExp(attr.validation.pattern).test(value)) {
            errors.set(attr.name, `${attr.label} has invalid format`);
          }
        }
        
        if (attr.type === 'number' && typeof value === 'number') {
          if (attr.validation?.min !== undefined && value < attr.validation.min) {
            errors.set(attr.name, `${attr.label} must be at least ${attr.validation.min}`);
          }
          if (attr.validation?.max !== undefined && value > attr.validation.max) {
            errors.set(attr.name, `${attr.label} must be at most ${attr.validation.max}`);
          }
        }
      });
    
    setValidationErrors(errors);
    return errors.size === 0;
  };

  /**
   * Handle save with optimistic updates and rollback on error
   * **Validates: Requirements 5.6, 8.1, 8.4, 12.1, 4.9**
   */
  const handleSave = async () => {
    // Validate all fields before save
    if (!validateAllFields()) {
      showError('Please fix validation errors before saving');
      return;
    }
    
    setIsSaving(true);
    
    // Store previous state for rollback
    const previousNode = node;
    
    try {
      // Optimistic UI update - update state immediately
      dispatch({ type: 'UPDATE_MIND', payload: formData });
      
      // Prepare update data (exclude readonly fields)
      // Base fields go at top level, type-specific fields go into type_specific_attributes
      const BASE_FIELDS = new Set(['title', 'description', 'status', 'tags', 'creator']);
      const updateData: Record<string, unknown> = {};
      const typeSpecificData: Record<string, unknown> = {};
      
      config.attributes
        .filter(attr => !attr.readonly)
        .forEach(attr => {
          const value = (formData as unknown as Record<string, unknown>)[attr.name];
          if (BASE_FIELDS.has(attr.name)) {
            updateData[attr.name] = value;
          } else {
            typeSpecificData[attr.name] = value;
          }
        });
      
      if (Object.keys(typeSpecificData).length > 0) {
        updateData.type_specific_attributes = typeSpecificData;
      }
      
      // Call API to update mind (creates new version)
      const updatedMind = await mindsAPI.update(node.uuid!, updateData);
      
      // Update state with response from backend (includes new version number)
      dispatch({ type: 'UPDATE_MIND', payload: updatedMind });
      
      // Reset dirty state
      setIsDirty(false);
      
      // Show success toast
      showSuccess('Changes saved successfully');
      
      // Announce CRUD operation
      announceCRUDOperation('updated', 'node', updatedMind.title);
      
    } catch (error) {
      // Rollback optimistic update on error
      dispatch({ type: 'UPDATE_MIND', payload: previousNode });
      
      // Display error toast
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to save changes';
      showError(errorMessage);
      console.error('Error saving mind:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData(node);
    setIsDirty(false);
    setValidationErrors(new Map());
  };

  /**
   * Handle delete with confirmation dialog
   * **Validates: Requirements 5.5, 5.6**
   */
  const handleDelete = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  const handleDeleteConfirm = async () => {
    setShowDeleteConfirm(false);
    setIsDeleting(true);

    try {
      // Call API to delete mind
      await mindsAPI.delete(node.uuid!);

      // Remove from graph state (also removes connected edges via cascade)
      dispatch({ type: 'DELETE_MIND', payload: node.uuid! });

      // Clear selection
      dispatch({ type: 'SELECT_NODE', payload: null });

      // Show success toast
      showSuccess(`${node.title} deleted successfully`);
      
      // Announce CRUD operation
      announceCRUDOperation('deleted', 'node', node.title);
    } catch (error) {
      // Display error toast
      const errorMessage = error instanceof Error
        ? error.message
        : 'Failed to delete node';
      showError(errorMessage);
      console.error('Error deleting mind:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  // Group attributes by category
  const readonlyAttrs = config.attributes.filter(attr => attr.readonly);
  const editableAttrs = config.attributes.filter(attr => !attr.readonly);

  // Helper to get attribute value from formData
  const getAttributeValue = (attrName: string): unknown => {
    return (formData as unknown as Record<string, unknown>)[attrName];
  };

  return (
    <div className="attribute-editor" role="region" aria-label="Node Attribute Editor">
      <div className="attribute-editor-header">
        <h2>Node Attributes</h2>
        <span className="node-type-badge" role="status">{nodeType}</span>
      </div>

      <div className="attribute-editor-content">
        {/* Read-only system attributes */}
        <section className="attribute-section" aria-labelledby="system-info-heading">
          <h3 id="system-info-heading">System Information</h3>
          {readonlyAttrs.map(attr => (
            <ReadOnlyField
              key={attr.name}
              label={attr.label}
              value={getAttributeValue(attr.name)}
              type={attr.type}
            />
          ))}
        </section>

        {/* Editable attributes */}
        <section className="attribute-section" aria-labelledby="editable-fields-heading">
          <h3 id="editable-fields-heading">Editable Fields</h3>
          {editableAttrs.map(attr => (
            <div key={attr.name}>
              <DynamicFormField
                config={attr}
                value={getAttributeValue(attr.name)}
                onChange={(value) => handleFieldChange(attr.name, value)}
              />
              {validationErrors.has(attr.name) && (
                <span className="error-message" role="alert">
                  {validationErrors.get(attr.name)}
                </span>
              )}
            </div>
          ))}
        </section>

        {/* Action buttons */}
        <div className="attribute-editor-actions" role="group" aria-label="Node actions">
          <button 
            className="btn btn-primary" 
            onClick={handleSave}
            disabled={!isDirty || isSaving || isDeleting}
            aria-label="Save changes to node"
            aria-busy={isSaving}
          >
            {isSaving && <Spinner size="small" label="Saving" />}
            {isSaving ? 'Saving...' : 'Save'}
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={handleCancel}
            disabled={!isDirty || isSaving || isDeleting}
            aria-label="Cancel changes"
          >
            Cancel
          </button>
          <button 
            className="btn btn-danger" 
            onClick={handleDelete}
            disabled={isSaving || isDeleting}
            aria-label="Delete node"
            aria-busy={isDeleting}
          >
            {isDeleting && <Spinner size="small" label="Deleting" />}
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Node"
        message={`Are you sure you want to delete "${node.title}"? This action cannot be undone. All relationships connected to this node will also be removed.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        danger={true}
      />
    </div>
  );
}

/**
 * RelationshipAttributeView Component
 * Displays all attributes of a selected relationship
 */
function RelationshipAttributeView({ relationship }: { relationship: { id: string; type: string; source: string; target: string; properties?: Record<string, unknown> } }) {
  const { state, dispatch } = useGraphEditor();
  const { showSuccess, showError } = useToast();
  const { minds } = state;

  const sourceNode = minds.get(relationship.source);
  const targetNode = minds.get(relationship.target);

  // Define expected properties per relationship type (keys must match backend storage names)
  const RELATIONSHIP_PROPERTY_SCHEMAS: Record<string, Record<string, { label: string; type: 'number' }>> = {
    CAN_OCCUR: {
      p1: { label: 'P1', type: 'number' },
      p2: { label: 'P2', type: 'number' },
    },
    LEAD_TO: {
      occurrence_probability: { label: 'Occurrence Probability', type: 'number' },
      detectability_probability: { label: 'Detectability Probability', type: 'number' },
    },
  };

  const schema = RELATIONSHIP_PROPERTY_SCHEMAS[relationship.type] ?? {};
  const schemaKeys = Object.keys(schema);

  // Build initial editable values from schema + actual properties
  const buildEditValues = (): Record<string, string> => {
    const values: Record<string, string> = {};
    const actual = relationship.properties ?? {};
    for (const key of schemaKeys) {
      const val = actual[key];
      values[key] = val !== null && val !== undefined && val !== '' ? String(val) : '';
    }
    return values;
  };

  const [editValues, setEditValues] = useState<Record<string, string>>(buildEditValues);
  const [isSaving, setIsSaving] = useState(false);

  // Reset edit values when the selected relationship changes
  useEffect(() => {
    setEditValues(buildEditValues());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [relationship.id, relationship.properties]);

  const handleFieldChange = (key: string, value: string): void => {
    setEditValues(prev => ({ ...prev, [key]: value }));
  };

  const hasChanges = (): boolean => {
    const actual = relationship.properties ?? {};
    for (const key of schemaKeys) {
      const current = actual[key];
      const currentStr = current !== null && current !== undefined && current !== '' ? String(current) : '';
      if (editValues[key] !== currentStr) return true;
    }
    return false;
  };

  const handleSave = async (): Promise<void> => {
    setIsSaving(true);
    try {
      // Build properties with parsed numeric values
      const updatedProps: Record<string, unknown> = { ...(relationship.properties ?? {}) };
      for (const key of schemaKeys) {
        const val = editValues[key];
        if (val === '') {
          updatedProps[key] = null;
        } else {
          const num = parseFloat(val);
          updatedProps[key] = isNaN(num) ? val : num;
        }
      }

      const updated = await relationshipsAPI.update(relationship.id, { properties: updatedProps });
      dispatch({ type: 'UPDATE_RELATIONSHIP', payload: updated });
      showSuccess('Relationship properties saved');
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to save relationship';
      showError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Also show any extra properties that exist on the relationship but aren't in the schema
  const extraProps = Object.entries(relationship.properties ?? {}).filter(
    ([key]) => !schemaKeys.includes(key)
  );

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined || value === '') return '—';
    if (Array.isArray(value)) return value.length > 0 ? value.join(', ') : '—';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  return (
    <div className="attribute-editor" role="region" aria-label="Relationship Attribute Editor">
      <div className="attribute-editor-header">
        <h2>Relationship Attributes</h2>
        <span className="relationship-type-badge" role="status">{relationship.type}</span>
      </div>

      <div className="attribute-editor-content">
        <section className="attribute-section" aria-labelledby="connection-heading">
          <h3 id="connection-heading">Connection</h3>
          <ReadOnlyField label="ID" value={relationship.id} />
          <ReadOnlyField label="Type" value={relationship.type} />
          <ReadOnlyField 
            label="Source" 
            value={sourceNode ? `${sourceNode.title} (${mindTypeToNodeType((sourceNode as any).mind_type)})` : relationship.source} 
          />
          <ReadOnlyField 
            label="Target" 
            value={targetNode ? `${targetNode.title} (${mindTypeToNodeType((targetNode as any).mind_type)})` : relationship.target} 
          />
        </section>

        {schemaKeys.length > 0 && (
          <section className="attribute-section" aria-labelledby="properties-heading">
            <h3 id="properties-heading">Properties</h3>
            {schemaKeys.map(key => {
              const fieldSchema = schema[key];
              return (
                <div key={key} className="attribute-field">
                  <label htmlFor={`rel-prop-${key}`}>{fieldSchema.label}</label>
                  <input
                    id={`rel-prop-${key}`}
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={editValues[key] ?? ''}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    className="form-input"
                    placeholder="0.0 – 1.0"
                    aria-label={fieldSchema.label}
                  />
                </div>
              );
            })}
          </section>
        )}

        {extraProps.length > 0 && (
          <section className="attribute-section" aria-labelledby="extra-properties-heading">
            <h3 id="extra-properties-heading">Other Properties</h3>
            {extraProps.map(([key, value]) => (
              <ReadOnlyField key={key} label={formatLabel(key)} value={formatValue(value)} />
            ))}
          </section>
        )}

        <div className="attribute-editor-actions" role="group" aria-label="Relationship actions">
          <button
            className="btn btn-primary"
            disabled={!hasChanges() || isSaving}
            onClick={handleSave}
            aria-label="Save relationship properties"
          >
            {isSaving ? 'Saving…' : 'Save'}
          </button>
          <button className="btn btn-danger" disabled aria-label="Delete relationship (not yet implemented)">
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * DynamicFormField Component
 * Renders the appropriate input component based on attribute configuration
 * 
 * **Validates: Requirements 4.5, 4.6**
 */
function DynamicFormField({
  config,
  value,
  onChange,
}: {
  config: AttributeConfig;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const fieldId = `field-${config.name}`;

  switch (config.type) {
    case 'string':
      return (
        <TextInput
          id={fieldId}
          label={config.label}
          value={(value as string) ?? ''}
          onChange={onChange}
          required={config.required}
          readonly={config.readonly}
          minLength={config.validation?.minLength}
          maxLength={config.validation?.maxLength}
          pattern={config.validation?.pattern}
          placeholder={config.placeholder}
          helpText={config.helpText}
          multiline={config.label.toLowerCase().includes('description') || 
                    config.label.toLowerCase().includes('content') ||
                    config.label.toLowerCase().includes('plan') ||
                    config.label.toLowerCase().includes('criteria')}
        />
      );

    case 'number':
      return (
        <NumberInput
          id={fieldId}
          label={config.label}
          value={value as number | null}
          onChange={onChange}
          required={config.required}
          readonly={config.readonly}
          min={config.validation?.min}
          max={config.validation?.max}
          placeholder={config.placeholder}
          helpText={config.helpText}
        />
      );

    case 'date':
      return (
        <DateInput
          id={fieldId}
          label={config.label}
          value={value as string | null}
          onChange={onChange}
          required={config.required}
          readonly={config.readonly}
          placeholder={config.placeholder}
          helpText={config.helpText}
        />
      );

    case 'datetime':
      // For datetime, show as read-only formatted text
      return (
        <ReadOnlyField
          label={config.label}
          value={value}
          type="datetime"
        />
      );

    case 'enum':
      return (
        <EnumInput
          id={fieldId}
          label={config.label}
          value={value as string | null}
          onChange={onChange}
          options={config.validation?.enumValues ?? []}
          required={config.required}
          readonly={config.readonly}
          placeholder={config.placeholder}
          helpText={config.helpText}
        />
      );

    case 'array':
      return (
        <ArrayInput
          id={fieldId}
          label={config.label}
          value={value as string[] | null}
          onChange={onChange}
          required={config.required}
          readonly={config.readonly}
          placeholder={config.placeholder}
          helpText={config.helpText}
        />
      );

    case 'boolean':
      return (
        <div className="form-input-wrapper">
          <label className="form-label" htmlFor={fieldId}>
            <input
              id={fieldId}
              type="checkbox"
              checked={Boolean(value)}
              onChange={(e) => onChange(e.target.checked)}
              disabled={config.readonly}
              style={{ marginRight: '0.5rem' }}
              aria-required={config.required}
              aria-describedby={config.helpText ? `${fieldId}-help` : undefined}
            />
            {config.label}
            {config.required && <span className="required-indicator" aria-label="required">*</span>}
          </label>
          {config.helpText && <span className="help-text" id={`${fieldId}-help`}>{config.helpText}</span>}
        </div>
      );

    default:
      return (
        <ReadOnlyField
          label={config.label}
          value={value}
          type="string"
        />
      );
  }
}

/**
 * ReadOnlyField Component
 * Displays a read-only attribute field
 */
function ReadOnlyField({ 
  label, 
  value,
  type = 'string'
}: { 
  label: string; 
  value: unknown;
  type?: 'string' | 'number' | 'date' | 'datetime' | 'boolean' | 'enum' | 'array';
}) {
  const formatValue = (val: unknown): string => {
    if (val === null || val === undefined) {
      return '—';
    }

    if (type === 'datetime' && typeof val === 'string') {
      return formatDateTime(val);
    }

    if (Array.isArray(val)) {
      return val.length > 0 ? val.join(', ') : '—';
    }

    if (typeof val === 'boolean') {
      return val ? 'Yes' : 'No';
    }

    if (typeof val === 'object') {
      return JSON.stringify(val, null, 2);
    }

    return String(val);
  };

  return (
    <div className="attribute-field readonly">
      <label className="attribute-label">{label}</label>
      <div className="attribute-value">{formatValue(value)}</div>
    </div>
  );
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format ISO 8601 datetime for display
 */
function formatDateTime(value: string | undefined): string {
  if (!value) return '—';
  
  try {
    const date = new Date(value);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return value;
  }
}

/**
 * Format label from snake_case or camelCase to Title Case
 */
function formatLabel(str: string): string {
  return str
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, s => s.toUpperCase())
    .trim();
}
