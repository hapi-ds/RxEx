/**
 * Type Adaptation Script for Mind Graph Editor
 * 
 * This script parses backend Python Pydantic models and generates TypeScript types.
 * It processes three backend files:
 * - backend/src/models/mind_types.py (specialized Mind types)
 * - backend/src/models/enums.py (enum definitions)
 * - backend/src/models/mind.py (base Mind model)
 * 
 * Generates: frontends/web/src/types/generated.ts
 * 
 * **Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.6**
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Type mapping from Python to TypeScript
const TYPE_MAPPING: Record<string, string> = {
  'str': 'string',
  'int': 'number',
  'float': 'number',
  'bool': 'boolean',
  'date': 'string', // ISO 8601 date string
  'datetime': 'string', // ISO 8601 datetime string
  'UUID': 'string',
  'EmailStr': 'string',
  'list[str]': 'string[]',
  'list[EmailStr]': 'string[]',
  'Optional[str]': 'string | null',
  'Optional[int]': 'number | null',
  'Optional[float]': 'number | null',
  'Optional[date]': 'string | null',
  'Optional[datetime]': 'string | null',
  'str | None': 'string | null',
  'list[str] | None': 'string[] | null',
};

interface EnumDefinition {
  name: string;
  values: Array<{ key: string; value: string }>;
}

interface FieldDefinition {
  name: string;
  type: string;
  required: boolean;
  description?: string;
}

interface ClassDefinition {
  name: string;
  primaryLabel: string;
  fields: FieldDefinition[];
}

/**
 * Parse enum definitions from enums.py
 */
function parseEnums(content: string): EnumDefinition[] {
  const enums: EnumDefinition[] = [];
  const enumPattern = /class\s+(\w+)\(.*?Enum\):\s*\n([\s\S]*?)(?=\n\nclass|\n\n$|$)/g;
  
  let match;
  while ((match = enumPattern.exec(content)) !== null) {
    const enumName = match[1];
    const enumBody = match[2];
    
    // Extract enum values
    const valuePattern = /^\s+(\w+)\s*=\s*["']([^"']+)["']/gm;
    const values: Array<{ key: string; value: string }> = [];
    
    let valueMatch;
    while ((valueMatch = valuePattern.exec(enumBody)) !== null) {
      values.push({
        key: valueMatch[1],
        value: valueMatch[2],
      });
    }
    
    if (values.length > 0) {
      enums.push({ name: enumName, values });
    }
  }
  
  return enums;
}

/**
 * Parse field definitions from a Pydantic class
 */
function parseFields(classBody: string, enumNames: Set<string>): FieldDefinition[] {
  const fields: FieldDefinition[] = [];
  
  // Remove docstrings first
  let cleanedBody = classBody.replace(/"""[\s\S]*?"""/g, '');
  cleanedBody = cleanedBody.replace(/'''[\s\S]*?'''/g, '');
  
  // Split into lines
  const lines = cleanedBody.split('\n');
  
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmedLine = line.trim();
    
    // Skip empty lines, comments, decorators, and methods
    if (!trimmedLine || 
        trimmedLine.startsWith('#') || 
        trimmedLine.startsWith('@') ||
        trimmedLine.startsWith('def ') ||
        trimmedLine.startsWith('class ')) {
      i++;
      continue;
    }
    
    // Match field definition: name: type (with optional = assignment)
    // Must have proper indentation (at least 4 spaces) and match Python field pattern
    const fieldMatch = /^\s{4,}(\w+):\s+([A-Za-z_][\w\[\]|,\s]*?)(?:\s*=\s*|$)/.exec(line);
    
    if (!fieldMatch) {
      i++;
      continue;
    }
    
    const fieldName = fieldMatch[1];
    let fieldType = fieldMatch[2].trim();
    
    // Skip special fields
    if (fieldName === '__primarylabel__' || fieldName === '__primaryproperty__') {
      i++;
      continue;
    }
    
    // Check if there's a Field() definition
    let fieldArgs = '';
    if (line.includes('Field(')) {
      // Collect the full Field() definition (might span multiple lines)
      let fullFieldDef = line;
      let j = i;
      let parenCount = (line.match(/\(/g) || []).length - (line.match(/\)/g) || []).length;
      
      while (parenCount > 0 && j < lines.length - 1) {
        j++;
        fullFieldDef += ' ' + lines[j].trim();
        parenCount += (lines[j].match(/\(/g) || []).length - (lines[j].match(/\)/g) || []).length;
      }
      
      // Extract Field arguments
      const fieldDefMatch = /Field\(([\s\S]*?)\)/.exec(fullFieldDef);
      if (fieldDefMatch) {
        fieldArgs = fieldDefMatch[1];
      }
      
      // Skip to the line after Field() closes
      i = j + 1;
    } else {
      i++;
    }
    
    // Determine if field is required
    const hasDefault = fieldArgs.includes('default=') || fieldArgs.includes('default_factory=');
    const isOptional = fieldType.includes('Optional[') || fieldType.includes('| None');
    const hasEllipsis = fieldArgs.trim().startsWith('...');
    const required = !hasDefault && !isOptional && hasEllipsis;
    
    // Extract description from Field arguments
    let description: string | undefined;
    const descMatch = /description\s*=\s*["']([^"']+)["']/.exec(fieldArgs);
    if (descMatch) {
      description = descMatch[1];
    }
    
    fields.push({
      name: fieldName,
      type: fieldType,
      required,
      description,
    });
  }
  
  return fields;
}

/**
 * Parse class definitions from Python files
 */
function parseClasses(content: string, enumNames: Set<string>): ClassDefinition[] {
  const classes: ClassDefinition[] = [];
  
  // Match class definitions
  const classPattern = /class\s+(\w+)\(BaseMind\):\s*\n([\s\S]*?)(?=\nclass\s|\n\n\nclass\s|$)/g;
  
  let match;
  while ((match = classPattern.exec(content)) !== null) {
    const className = match[1];
    const classBody = match[2];
    
    // Extract __primarylabel__
    const labelMatch = /__primarylabel__:\s*str\s*=\s*["']([^"']+)["']/.exec(classBody);
    const primaryLabel = labelMatch ? labelMatch[1] : className;
    
    // Parse fields
    const fields = parseFields(classBody, enumNames);
    
    classes.push({
      name: className,
      primaryLabel,
      fields,
    });
  }
  
  return classes;
}

/**
 * Parse BaseMind class from mind.py
 */
function parseBaseMind(content: string, enumNames: Set<string>): FieldDefinition[] {
  const classMatch = /class\s+BaseMind\(BaseNode\):\s*\n([\s\S]*?)(?=\nclass\s|$)/.exec(content);
  
  if (!classMatch) {
    throw new Error('BaseMind class not found in mind.py');
  }
  
  return parseFields(classMatch[1], enumNames);
}

/**
 * Map Python type to TypeScript type
 */
function mapType(pythonType: string, enumNames: Set<string>): string {
  // Check if it's an enum type
  if (enumNames.has(pythonType)) {
    return pythonType;
  }
  
  // Check direct mapping
  if (TYPE_MAPPING[pythonType]) {
    return TYPE_MAPPING[pythonType];
  }
  
  // Handle Optional types
  if (pythonType.startsWith('Optional[')) {
    const innerType = pythonType.slice(9, -1);
    const mappedInner = mapType(innerType, enumNames);
    return `${mappedInner} | null`;
  }
  
  // Handle list types
  if (pythonType.startsWith('list[')) {
    const innerType = pythonType.slice(5, -1);
    const mappedInner = mapType(innerType, enumNames);
    return `${mappedInner}[]`;
  }
  
  // Handle union types with None
  if (pythonType.includes(' | None')) {
    const baseType = pythonType.replace(' | None', '').trim();
    const mappedBase = mapType(baseType, enumNames);
    return `${mappedBase} | null`;
  }
  
  // Default to any for unknown types
  console.warn(`Unknown type: ${pythonType}, mapping to 'any'`);
  return 'any';
}

/**
 * Generate TypeScript enum definition as const object + type union
 * (compatible with erasableSyntaxOnly)
 */
function generateEnum(enumDef: EnumDefinition): string {
  const lines: string[] = [];
  
  // Generate type union
  const values = enumDef.values.map(({ value }) => `'${value}'`).join(' | ');
  lines.push(`export type ${enumDef.name} = ${values};`);
  lines.push('');
  
  // Generate const object for runtime access
  lines.push(`export const ${enumDef.name} = {`);
  enumDef.values.forEach(({ key, value }) => {
    lines.push(`  ${key}: '${value}' as const,`);
  });
  lines.push(`} as const;`);
  
  return lines.join('\n');
}

/**
 * Generate TypeScript interface definition
 */
function generateInterface(
  classDef: ClassDefinition,
  baseFields: FieldDefinition[],
  enumNames: Set<string>
): string {
  const lines = [`export interface ${classDef.name} {`];
  
  // Add __primarylabel__ field
  lines.push(`  __primarylabel__: '${classDef.primaryLabel}';`);
  
  // Create a set of class-specific field names to avoid duplicates
  const classFieldNames = new Set(classDef.fields.map(f => f.name));
  
  // Add base fields (skip if overridden by class-specific fields)
  baseFields.forEach(field => {
    if (!classFieldNames.has(field.name)) {
      const tsType = mapType(field.type, enumNames);
      const optional = !field.required ? '?' : '';
      const comment = field.description ? ` // ${field.description}` : '';
      lines.push(`  ${field.name}${optional}: ${tsType};${comment}`);
    }
  });
  
  // Add class-specific fields
  classDef.fields.forEach(field => {
    const tsType = mapType(field.type, enumNames);
    const optional = !field.required ? '?' : '';
    const comment = field.description ? ` // ${field.description}` : '';
    lines.push(`  ${field.name}${optional}: ${tsType};${comment}`);
  });
  
  lines.push('}');
  
  return lines.join('\n');
}

/**
 * Generate union type for all Mind types
 */
function generateMindUnion(classes: ClassDefinition[]): string {
  const typeNames = classes.map(c => c.name).join(' | ');
  return `export type Mind = ${typeNames};`;
}

/**
 * Generate NodeType union
 */
function getBackendTypeName(className: string): string {
  // Special cases where the type name doesn't match the class name directly
  const specialCases: Record<string, string> = {
    AcceptanceCriteria: 'acceptance_criteria',
  };
  
  return specialCases[className] || className.toLowerCase();
}

function generateNodeType(classes: ClassDefinition[]): string {
  // Use lowercase type names that match backend MIND_TYPE_MAP
  const labels = classes.map(c => `'${getBackendTypeName(c.name)}'`).join(' | ');
  return `export type NodeType = ${labels};`;
}

/**
 * Main generation function
 */
function generateTypes(): void {
  console.log('Starting type generation...');
  
  // Resolve paths
  const backendPath = path.resolve(__dirname, '../../../backend/src/models');
  const outputPath = path.resolve(__dirname, '../src/types/generated.ts');
  
  // Read backend files
  console.log('Reading backend files...');
  const enumsContent = fs.readFileSync(path.join(backendPath, 'enums.py'), 'utf-8');
  const mindContent = fs.readFileSync(path.join(backendPath, 'mind.py'), 'utf-8');
  const mindTypesContent = fs.readFileSync(path.join(backendPath, 'mind_types.py'), 'utf-8');
  
  // Parse enums
  console.log('Parsing enums...');
  const enums = parseEnums(enumsContent);
  const enumNames = new Set(enums.map(e => e.name));
  
  // Parse BaseMind
  console.log('Parsing BaseMind...');
  const baseFields = parseBaseMind(mindContent, enumNames);
  
  // Parse specialized Mind types
  console.log('Parsing Mind types...');
  const classes = parseClasses(mindTypesContent, enumNames);
  
  // Generate TypeScript code
  console.log('Generating TypeScript code...');
  const output: string[] = [];
  
  // Header
  output.push('/**');
  output.push(' * Auto-generated TypeScript types from backend Python models');
  output.push(' * DO NOT EDIT MANUALLY - Generated by scripts/generate-types.ts');
  output.push(' * ');
  output.push(' * Source files:');
  output.push(' * - backend/src/models/mind_types.py');
  output.push(' * - backend/src/models/enums.py');
  output.push(' * - backend/src/models/mind.py');
  output.push(' * ');
  output.push(' * **Validates: Requirements 10.5, 10.6, 10.8, 10.9**');
  output.push(' */');
  output.push('');
  
  // Generate enums
  output.push('// ============================================================================');
  output.push('// Enums');
  output.push('// ============================================================================');
  output.push('');
  
  enums.forEach(enumDef => {
    output.push(generateEnum(enumDef));
    output.push('');
  });
  
  // Generate interfaces
  output.push('// ============================================================================');
  output.push('// Mind Type Interfaces');
  output.push('// ============================================================================');
  output.push('');
  
  classes.forEach(classDef => {
    output.push(generateInterface(classDef, baseFields, enumNames));
    output.push('');
  });
  
  // Generate union types
  output.push('// ============================================================================');
  output.push('// Union Types');
  output.push('// ============================================================================');
  output.push('');
  output.push(generateMindUnion(classes));
  output.push('');
  output.push(generateNodeType(classes));
  output.push('');
  
  // Write output file
  console.log(`Writing output to ${outputPath}...`);
  fs.writeFileSync(outputPath, output.join('\n'), 'utf-8');
  
  console.log('✓ Type generation complete!');
  console.log(`  Generated ${enums.length} enums`);
  console.log(`  Generated ${classes.length} interfaces`);
  console.log(`  Output: ${outputPath}`);
}

// Run the script
try {
  generateTypes();
} catch (error) {
  console.error('Error generating types:', error);
  process.exit(1);
}
