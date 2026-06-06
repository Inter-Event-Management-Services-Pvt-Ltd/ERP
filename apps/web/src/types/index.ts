/**
 * Roles match the uppercase strings returned by GET /v1/me and GET /v1/me/permissions.
 * Never read role from Supabase user_metadata — always use the backend response.
 */
export type UserRole =
  | 'EMPLOYEE'
  | 'MANAGER'
  | 'ADMIN'
  | 'SUPER_ADMIN'
  | 'SUPER_USER'
  | 'DIRECTOR'

/** Shape of GET /v1/me */
export interface MeResponse {
  auth_user_id: string
  account: {
    is_active: boolean
    is_super_user: boolean
  }
  employee: {
    id: string
    employee_code: string
    full_name: string
    official_email: string
    designation: string
    employment_status: string
  }
  roles: UserRole[]
  permissions: string[]
}

/** Shape of GET /v1/me/permissions */
export interface PermissionsResponse {
  roles: UserRole[]
  permissions: string[]
  is_super_user: boolean
  super_user_requires_reason: boolean
}

/** Resolved user context held in React Query cache */
export interface AuthUser {
  supabaseId: string
  employeeId: string
  employeeCode: string
  fullName: string
  email: string
  designation: string
  roles: UserRole[]
  permissions: string[]
  isActive: boolean
  isSuperUser: boolean
}

export type BadgeVariant =
  | 'active'
  | 'pending'
  | 'overdue'
  | 'approved'
  | 'rejected'
  | 'archived'
  | 'info'
  | 'warning'
  | 'critical'

export type Severity = 'critical' | 'high' | 'normal' | 'info'

/** API error envelope — matches backend contract */
export interface ApiError {
  error: {
    code: string
    message: string
    request_id?: string
  }
}

// ─── Clients ──────────────────────────────────────────────────────────────────

export interface Client {
  id: string
  client_code: string
  legal_name: string
  display_name: string
  is_active: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CreateClientPayload {
  client_code: string
  legal_name: string
  display_name: string
  notes?: string
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export interface ProjectClient {
  id: string
  client_code: string
  display_name: string
}

export interface ProjectLookup {
  id: string
  code: string
  name: string
}

export interface Project {
  id: string
  project_code: string
  client_id: string
  client: ProjectClient
  project_type_id: string
  project_type: ProjectLookup
  project_status_id: string
  project_status: ProjectLookup
  priority_level_id: string
  priority_level: ProjectLookup
  name: string
  event_date: string
  venue: string
  description: string | null
  project_manager_id: string
  created_by: string
  created_at: string
  updated_at: string
  archived_at: string | null
  deleted_at: string | null
  root_folder_id: string
}

export interface CreateProjectPayload {
  project_code: string
  name: string
  client_id: string
  project_type_id: string
  project_status_id: string
  priority_level_id: string
  event_date: string
  venue: string
  description?: string
}

export interface UpdateProjectPayload {
  name?: string
  event_date?: string
  venue?: string
  description?: string
  project_status_id?: string
  priority_level_id?: string
}

export type ProjectMemberRole = 'VIEW' | 'CONTRIBUTE' | 'MANAGE'

export interface ProjectMember {
  project_id: string
  employee_id: string
  employee: {
    id: string
    employee_code: string
    full_name: string
  }
  access_level: ProjectMemberRole
  assigned_by: string
  assigned_at: string
  removed_at: string | null
}

export interface AddProjectMemberPayload {
  employee_id: string
  access_level: ProjectMemberRole
}

export interface UpdateProjectMemberPayload {
  access_level: ProjectMemberRole
}

export interface ReferenceLookup {
  id: string
  code: string
  name: string
}

// ─── Folders ──────────────────────────────────────────────────────────────────

export interface FolderNode {
  id: string
  project_id: string
  parent_folder_id: string | null
  name: string
  sort_order: number
  children: FolderNode[]
}

// ─── Employees (used in member picker) ────────────────────────────────────────

export interface EmployeeSummary {
  id: string
  employee_code: string
  full_name: string
  official_email: string
  designation: string
  employment_status: string
}
