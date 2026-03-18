/**
 * CreateNodeForm Component
 * Form for creating a new node with dynamic fields based on node type
 * 
 * Features:
 * - Renders form fields based on NodeTypeConfig
 * - Validates required fields (title, creator)
 * - Calls mindsAPI.create on submit
 * - Adds new node to graph state
 * - Shows success/error toast notifications
 * 
 * **Validates: Requirements 5.1, 5.3, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7, 21.8, 21.9, 21.10, 21.11**
 */

import { useState } from 'react';
import { useGraphEditor } from './GraphEditorContext';
import { useToast } from './ToastContext';
import { useScreenReaderAnnouncer } from './ScreenReaderAnnouncer';
import type { Mind, NodeType } from '../../types/generated';
import { getNodeTypeConfig, BASE_ATTRIBUTE_NAMES } from './nodeTypeConfig';
import type { AttributeConfig } from './nodeTypeConfig';
import { TextInput, NumberInput, DateInput, EnumInput, ArrayInput } from './form-inputs';
import { mindsAPI } from '../../services/api';
import './CreateNodeForm.css';

export interface CreateNodeFormProps {
  nodeType: NodeType;
  onSuccess: (createdNode: Mind) => void;
  onCancel: () => void;
}

/**
 * CreateNodeForm Component
 * Displays a form for creating a new node of the specified type
 */
export function CreateNodeForm({ nodeType, onSuccess, onCancel }: CreateNodeFormProps) {
  const { dispatch } = useGraphEditor();
  const { showSuccess, showError } = useToast();
  const { announceCRUDOperation } = useScreenReaderAnnouncer();
  const config = getNodeTypeConfig(nodeType);
  
  // Initialize form data with default values
  const [formData, setFormData] = useState<Record<string, unknown>>(() => {
    const initial: Record<string, unknown> = {
      // Don't set __primarylabel__ - backend will handle it
    };
    
    // Set default values for required fields
    config.attributes
      .filter(attr => !attr.readonly)
      .forEach(attr => {
        if (attr.type === 'array') {
          initial[attr.name] = [];
        } else if (attr.type === 'boolean') {
          initial[attr.name] = false;
        } else {
          initial[attr.name] = null;
        }
      });
    
    return initial;
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Map<string, string>>(new Map());

  const handleFieldChange = (fieldName: string, value: unknown) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
    
    // Clear validation error for this field when user makes changes
    if (validationErrors.has(fieldName)) {
      const newErrors = new Map(validationErrors);
      newErrors.delete(fieldName);
      setValidationErrors(newErrors);
    }
  };

  /**
   * Validate all fields before submission
   * **Validates: Requirements 21.6, 21.7**
   */
  const validateAllFields = (): boolean => {
    const errors = new Map<string, string>();
    
    config.attributes
      .filter(attr => !attr.readonly)
      .forEach(attr => {
        const value = formData[attr.name];
        
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
   * Handle form submission
   * **Validates: Requirements 21.9, 21.10, 21.11, 21.15**
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate all fields before submission
    if (!validateAllFields()) {
      showError('Please fix validation errors before creating the node');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Prepare create data with mind_type and nested type_specific_attributes
      const createData: Record<string, unknown> = {
        mind_type: config.type,
      };
      const typeSpecificAttributes: Record<string, unknown> = {};

      // Readonly base attribute names to exclude from payload
      const readonlyBaseNames = new Set(['uuid', 'version', 'created_at', 'updated_at']);
      
      config.attributes
        .filter(attr => !attr.readonly)
        .forEach(attr => {
          const value = formData[attr.name];
          // Only include if required or has a non-empty value
          if (attr.required || (value !== null && value !== undefined && value !== '')) {
            if (BASE_ATTRIBUTE_NAMES.has(attr.name) && !readonlyBaseNames.has(attr.name)) {
              // Base field — top level
              createData[attr.name] = value;
            } else if (!BASE_ATTRIBUTE_NAMES.has(attr.name)) {
              // Type-specific field — nested
              typeSpecificAttributes[attr.name] = value;
            }
          }
        });

      // Only include type_specific_attributes if there are any
      if (Object.keys(typeSpecificAttributes).length > 0) {
        createData.type_specific_attributes = typeSpecificAttributes;
      }
      
      // Call API to create mind
      const createdMind = await mindsAPI.create(createData as Omit<Mind, 'uuid' | 'version' | 'created_at' | 'updated_at'>);
      
      // Add new node to graph state
      dispatch({ type: 'ADD_MIND', payload: createdMind });
      
      // Select the newly created node
      dispatch({ type: 'SELECT_NODE', payload: createdMind.uuid! });
      
      // Show success toast
      showSuccess(`${config.label} created successfully`);
      
      // Announce CRUD operation
      announceCRUDOperation('created', 'node', createdMind.title);
      
      // Call success callback (closes modal)
      onSuccess(createdMind);
      
    } catch (error) {
      // Display error toast
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to create node';
      showError(errorMessage);
      console.error('Error creating mind:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get editable attributes (exclude readonly system fields)
  const editableAttrs = config.attributes.filter(attr => !attr.readonly);

  return (
    <form className="create-node-form" onSubmit={handleSubmit} aria-labelledby="create-node-form-title">
      <div className="create-node-form-header">
        <h3 id="create-node-form-title">Create {config.label}</h3>
        <span className="node-type-badge" role="status">{nodeType}</span>
      </div>

      <div className="create-node-form-content">
        {editableAttrs.map(attr => (
          <div key={attr.name} className="form-field-wrapper">
            <DynamicFormField
              config={attr}
              value={formData[attr.name]}
              onChange={(value) => handleFieldChange(attr.name, value)}
            />
            {validationErrors.has(attr.name) && (
              <span className="error-message" role="alert">
                {validationErrors.get(attr.name)}
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="create-node-form-actions" role="group" aria-label="Form actions">
        <button 
          type="submit"
          className="btn btn-primary" 
          disabled={isSubmitting}
          aria-label="Create node"
        >
          {isSubmitting ? 'Creating...' : 'Create'}
        </button>
        <button 
          type="button"
          className="btn btn-secondary" 
          onClick={onCancel}
          disabled={isSubmitting}
          aria-label="Cancel node creation"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

/**
 * DynamicFormField Component
 * Renders the appropriate input component based on attribute configuration
 * 
 * **Validates: Requirements 21.5**
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
  const fieldId = `create-field-${config.name}`;

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
                    config.label.toLowerCase().includes('criteria') ||
                    config.label.toLowerCase().includes('text')}
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
        <TextInput
          id={fieldId}
          label={config.label}
          value={String(value ?? '')}
          onChange={onChange}
          required={config.required}
          readonly={config.readonly}
          placeholder={config.placeholder}
          helpText={config.helpText}
        />
      );
  }
}
