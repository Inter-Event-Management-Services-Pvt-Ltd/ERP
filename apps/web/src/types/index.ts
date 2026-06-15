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
  archived_at?: string | null
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

export interface CreateFolderPayload {
  name: string
  parent_folder_id?: string
}

export interface UpdateFolderPayload {
  name: string
}

// ─── Documents ────────────────────────────────────────────────────────────────

export interface DocumentVersion {
  id: string
  version_number: number
  storage_bucket: string
  storage_key: string
  original_filename: string
  mime_type: string
  size_bytes: number
  checksum_sha256: string
  preview_supported: boolean
}

export interface Document {
  id: string
  project_id: string
  folder_id: string
  document_type_id: string | null
  confidentiality_level_id: string
  display_name: string
  status: string
  latest_version: DocumentVersion | null
  created_at: string
  updated_at: string
}

export interface DownloadUrlResponse {
  url: string
  expires_in_seconds: number
  expires_at: string
}

// ─── Archive exports ──────────────────────────────────────────────────────────

export type ExportStatus = 'QUEUED' | 'GENERATING' | 'READY' | 'FAILED' | 'EXPIRED' | 'CANCELLED'

export interface ArchiveExport {
  id: string
  project_id: string
  status: ExportStatus
  requested_by: string
  requested_at: string
  completed_at: string | null
  file_size_bytes: number | null
  error_message: string | null
}

// ─── Physical archive ─────────────────────────────────────────────────────────

export interface PhysicalRoom {
  id: string
  code: string
  name: string
  description: string | null
  is_active: boolean
}

export interface CreatePhysicalRoomPayload {
  code: string
  name: string
  description?: string
}

export type PhysicalLocationType = 'RACK' | 'SHELF' | 'CABINET' | 'BOX' | 'FILE_SLOT'

export interface PhysicalLocation {
  id: string
  archive_room_id: string
  parent_location_id: string | null
  location_type: PhysicalLocationType
  code: string
  label: string | null
  qr_token: string
  is_active: boolean
}

export interface CreatePhysicalLocationPayload {
  archive_room_id: string
  parent_location_id?: string
  location_type: PhysicalLocationType
  code: string
  label?: string
}

export type PhysicalFileState = 'AVAILABLE' | 'CHECKED_OUT' | 'MISSING' | 'UNDER_VERIFICATION' | 'ARCHIVED'

export interface PhysicalArchiveProjectSummary {
  id: string
  project_code: string
  name: string
}

export interface PhysicalArchiveLocationSummary {
  id: string
  archive_room_id: string
  location_type: PhysicalLocationType
  code: string
  label: string | null
  qr_token: string
}

export interface PhysicalArchiveRoomSummary {
  id: string
  code: string
  name: string
}

export interface PhysicalFileCheckout {
  id: string
  checked_out_by: string
  checked_out_at: string
  purpose: string
  expected_return_at: string | null
}

export interface PhysicalFile {
  id: string
  physical_file_code: string
  project_id: string
  project: PhysicalArchiveProjectSummary | null
  archive_location_id: string
  archive_location: PhysicalArchiveLocationSummary | null
  archive_room: PhysicalArchiveRoomSummary | null
  volume_number: number
  status: PhysicalFileState
  qr_token: string
  archived_on: string | null
  archived_by: string | null
  last_verified_at: string | null
  next_verification_at: string | null
  notes: string | null
  open_checkout: PhysicalFileCheckout | null
  created_at: string
  updated_at: string
}

export interface CreatePhysicalFilePayload {
  physical_file_code: string
  archive_location_id: string
  volume_number?: number
  archived_on?: string
  notes?: string
}

export interface PhysicalFileCheckoutPayload {
  purpose: string
  expected_return_at?: string
}

export interface PhysicalFileReturnPayload {
  returned_to_location_id?: string
  remarks?: string
}

export interface PhysicalFileMovePayload {
  to_location_id: string
  remarks?: string
}

export interface PhysicalFileVerifyPayload {
  location_correct: boolean
  label_readable: boolean
  physical_file_present: boolean
  digital_archive_present: boolean
  documents_complete: boolean
  remarks?: string
}

export interface PhysicalFileLabel {
  physical_file_id: string
  physical_file_code: string
  project_code: string
  project_name: string
  location_code: string
  archive_room: string
  qr_token: string
  label_text: string
}

export interface PhysicalLocationContents {
  location: PhysicalLocation
  child_locations: PhysicalLocation[]
  physical_files: PhysicalFile[]
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

// ─── Attendance ───────────────────────────────────────────────────────────────

export type AttendanceSource = 'WEB' | 'MOBILE' | 'ADMIN' | 'QR' | 'BIOMETRIC' | 'IMPORT'

export interface AttendanceEmployeeSummary {
  id: string
  employee_code: string
  full_name: string
}

export interface AttendanceSession {
  id: string
  employee_id: string
  employee: AttendanceEmployeeSummary | null
  checked_in_at: string
  checked_out_at: string | null
  source: AttendanceSource
  remarks: string | null
  created_by: string
  corrected_by: string | null
  correction_reason: string | null
  created_at: string
  updated_at: string
  total_minutes: number | null
}

export interface CheckInPayload {
  remarks?: string
}

export interface CheckOutPayload {
  remarks?: string
}

export interface AttendanceCorrectionPayload {
  checked_in_at?: string
  checked_out_at?: string
  remarks?: string
  correction_reason: string
}

export interface DirectorAttendanceSummary {
  employee_id: string
  employee_code: string
  full_name: string
  first_check_in: string | null
  last_check_out: string | null
  total_minutes: number | null
  attendance_state: string
}

// ─── Leave ────────────────────────────────────────────────────────────────────

export type LeaveStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED'

export interface LeaveRequest {
  id: string
  employee_id: string
  employee: AttendanceEmployeeSummary | null
  leave_type_id: string
  leave_type: ReferenceLookup | null
  start_date: string
  end_date: string
  reason: string
  status: LeaveStatus
  requested_at: string
  reviewed_by: string | null
  reviewed_at: string | null
  review_comment: string | null
}

export interface CreateLeaveRequestPayload {
  leave_type_id: string
  start_date: string
  end_date: string
  reason: string
}

export interface ReviewLeaveRequestPayload {
  review_comment?: string
}

// ─── Tasks ────────────────────────────────────────────────────────────────────

export type TaskStatusCode = 'TODO' | 'IN_PROGRESS' | 'BLOCKED' | 'COMPLETED' | 'CANCELLED'

export interface TaskProjectSummary {
  id: string
  project_code: string
  name: string
}

export interface Task {
  id: string
  project_id: string | null
  project: TaskProjectSummary | null
  related_folder_id: string | null
  title: string
  description: string | null
  task_status_id: string
  task_status: ReferenceLookup | null
  priority_level_id: string
  priority_level: ReferenceLookup | null
  created_by: string
  due_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
  assignees: EmployeeSummary[]
  document_ids: string[]
}

export interface CreateTaskPayload {
  project_id?: string | null
  related_folder_id?: string | null
  title: string
  description?: string
  task_status_id?: string | null
  priority_level_id: string
  due_at?: string | null
  assignee_ids?: string[]
  document_ids?: string[]
}

export interface UpdateTaskPayload {
  project_id?: string | null
  related_folder_id?: string | null
  title?: string
  description?: string
  task_status_id?: string | null
  priority_level_id?: string
  due_at?: string | null
}

export interface AddTaskAssigneesPayload {
  employee_ids: string[]
}

export interface AddTaskCommentPayload {
  comment_text: string
}

export interface TaskComment {
  id: string
  task_id: string
  employee_id: string
  employee: EmployeeSummary | null
  comment_text: string
  created_at: string
  edited_at: string | null
}

export interface LinkTaskDocumentPayload {
  document_id: string
}

// ─── Calendar ─────────────────────────────────────────────────────────────────

export type CalendarEventType =
  | 'MEETING'
  | 'SITE_VISIT'
  | 'EVENT'
  | 'DEADLINE'
  | 'LEAVE'
  | 'ARCHIVE_VERIFICATION'
  | 'PHYSICAL_FILE_RETURN'
  | 'REMINDER'

export type CalendarEventSource = 'CALENDAR_EVENT' | 'TASK_DEADLINE' | 'LEAVE' | 'PHYSICAL_FILE_RETURN'

export interface CalendarEvent {
  id: string
  event_type: CalendarEventType
  title: string
  description: string | null
  starts_at: string
  ends_at: string | null
  location: string | null
  project_id: string | null
  related_task_id: string | null
  created_by: string | null
  created_at: string | null
  updated_at: string | null
  source: CalendarEventSource
}

export interface CreateCalendarEventPayload {
  project_id?: string | null
  related_task_id?: string | null
  event_type: CalendarEventType
  title: string
  description?: string
  starts_at: string
  ends_at?: string
  location?: string
  attendee_ids?: string[]
}

export interface UpdateCalendarEventPayload {
  title?: string
  description?: string
  starts_at?: string
  ends_at?: string
  location?: string
}
