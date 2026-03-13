/**
 * Utility functions for converting mind_type strings
 */

/**
 * Converts backend mind_type format to frontend NodeType format
 * Examples:
 *   "project" -> "Project"
 *   "acceptance_criteria" -> "AcceptanceCriteria"
 *   "schedule_history" -> "ScheduleHistory"
 */
export function mindTypeToNodeType(mindType: string | undefined): string {
  if (!mindType) return 'Knowledge'; // Default fallback
  
  // Split on underscores and capitalize each word
  return mindType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('');
}
