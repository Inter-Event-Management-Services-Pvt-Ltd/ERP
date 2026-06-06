export function apiErrorMessage(err: unknown): string {
  const code = (err as { code?: string })?.code
  switch (code) {
    case 'INVALID_FILE_NAME':
      return 'File name is not allowed. Rename the file and try again.'
    case 'INVALID_MIME_TYPE':
      return 'This file type is not supported.'
    case 'INVALID_FILE_SIZE':
      return 'File is too large or empty.'
    case 'INVALID_STATE':
      return 'This action is not allowed in the current state.'
    case 'INVALID_REFERENCE':
      return 'A referenced item no longer exists or is inactive.'
    case 'RESOURCE_CONFLICT':
      return 'A conflict prevents this action. The name may already be in use.'
    case 'INVALID_PHYSICAL_FILE_STATE':
      return 'This physical file cannot perform that action in its current state.'
    case 'INVALID_PROJECT_MEMBER_STATE':
      return 'Project must retain at least one manager.'
    case 'PERMISSION_DENIED':
    case 'ABAC_DENIED':
      return 'You do not have permission to perform this action.'
    default:
      return (err instanceof Error && err.message) ? err.message : 'An unexpected error occurred.'
  }
}
