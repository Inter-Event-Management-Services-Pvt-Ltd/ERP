import { createClient as createSupabaseClient } from '@/lib/supabase/client'
import type {
  MeResponse,
  PermissionsResponse,
  Client,
  CreateClientPayload,
  Project,
  CreateProjectPayload,
  UpdateProjectPayload,
  ProjectMember,
  AddProjectMemberPayload,
  UpdateProjectMemberPayload,
  ReferenceLookup,
  FolderNode,
  CreateFolderPayload,
  UpdateFolderPayload,
  Document,
  DownloadUrlResponse,
  ArchiveExport,
  PhysicalRoom,
  CreatePhysicalRoomPayload,
  PhysicalLocation,
  CreatePhysicalLocationPayload,
  PhysicalLocationContents,
  PhysicalFile,
  CreatePhysicalFilePayload,
  PhysicalFileCheckoutPayload,
  PhysicalFileReturnPayload,
  PhysicalFileMovePayload,
  PhysicalFileVerifyPayload,
  PhysicalFileLabel,
  EmployeeSummary,
  AttendanceSession,
  CheckInPayload,
  CheckOutPayload,
  AttendanceCorrectionPayload,
  DirectorAttendanceSummary,
  LeaveRequest,
  CreateLeaveRequestPayload,
  ReviewLeaveRequestPayload,
  Task,
  CreateTaskPayload,
  UpdateTaskPayload,
  AddTaskAssigneesPayload,
  AddTaskCommentPayload,
  TaskComment,
  LinkTaskDocumentPayload,
  CalendarEvent,
  CreateCalendarEventPayload,
  UpdateCalendarEventPayload,
  DirectorOverview,
  DirectorProject,
  DirectorApproval,
  DirectorOverdueTask,
  DirectorCheckedOutFile,
  DirectorAuditEvent,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function getAccessToken(): Promise<string> {
  const supabase = createSupabaseClient()
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('No active session')
  return token
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAccessToken()
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const code = body?.error?.code ?? `HTTP_${res.status}`
    const message = body?.error?.message ?? res.statusText
    throw Object.assign(new Error(message), { code, status: res.status })
  }

  return res.json() as Promise<T>
}

/** Multipart upload — browser sets Content-Type with boundary automatically. */
async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const token = await getAccessToken()
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const code = body?.error?.code ?? `HTTP_${res.status}`
    const message = body?.error?.message ?? res.statusText
    throw Object.assign(new Error(message), { code, status: res.status })
  }
  return res.json() as Promise<T>
}

export async function fetchMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>('/v1/me')
}

export async function fetchPermissions(): Promise<PermissionsResponse> {
  return apiFetch<PermissionsResponse>('/v1/me/permissions')
}

// ─── Clients ──────────────────────────────────────────────────────────────────

export async function fetchClients(): Promise<Client[]> {
  return apiFetch<Client[]>('/v1/clients')
}

export async function fetchClient(id: string): Promise<Client> {
  return apiFetch<Client>(`/v1/clients/${id}`)
}

export async function createClient(payload: CreateClientPayload): Promise<Client> {
  return apiFetch<Client>('/v1/clients', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateClient(
  id: string,
  payload: Partial<CreateClientPayload>
): Promise<Client> {
  return apiFetch<Client>(`/v1/clients/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deactivateClient(id: string): Promise<void> {
  await apiFetch<unknown>(`/v1/clients/${id}`, { method: 'DELETE' })
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export async function fetchProjects(options?: { includeArchived?: boolean }): Promise<Project[]> {
  const query = options?.includeArchived ? '?include_archived=true' : ''
  return apiFetch<Project[]>(`/v1/projects${query}`)
}

export async function fetchProject(id: string): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${id}`)
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  return apiFetch<Project>('/v1/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateProject(
  id: string,
  payload: UpdateProjectPayload
): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function fetchProjectMembers(projectId: string): Promise<ProjectMember[]> {
  return apiFetch<ProjectMember[]>(`/v1/projects/${projectId}/members`)
}

export async function addProjectMember(
  projectId: string,
  payload: AddProjectMemberPayload
): Promise<void> {
  await apiFetch<unknown>(`/v1/projects/${projectId}/members`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function removeProjectMember(
  projectId: string,
  employeeId: string
): Promise<void> {
  await apiFetch<unknown>(`/v1/projects/${projectId}/members/${employeeId}`, {
    method: 'DELETE',
  })
}

export async function updateProjectMemberRole(
  projectId: string,
  employeeId: string,
  payload: UpdateProjectMemberPayload
): Promise<void> {
  await apiFetch<unknown>(`/v1/projects/${projectId}/members/${employeeId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

// ─── Reference lookups ────────────────────────────────────────────────────────

export async function fetchProjectTypes(): Promise<ReferenceLookup[]> {
  return apiFetch<ReferenceLookup[]>('/v1/project-types')
}

export async function fetchProjectStatuses(): Promise<ReferenceLookup[]> {
  return apiFetch<ReferenceLookup[]>('/v1/project-statuses')
}

export async function fetchPriorityLevels(): Promise<ReferenceLookup[]> {
  return apiFetch<ReferenceLookup[]>('/v1/priority-levels')
}

// ─── Folders ──────────────────────────────────────────────────────────────────

export async function fetchFolderTree(projectId: string): Promise<FolderNode> {
  return apiFetch<FolderNode>(`/v1/projects/${projectId}/folders/tree`)
}

export async function createFolder(
  projectId: string,
  payload: CreateFolderPayload
): Promise<FolderNode> {
  return apiFetch<FolderNode>(`/v1/projects/${projectId}/folders`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function renameFolder(
  folderId: string,
  payload: UpdateFolderPayload
): Promise<FolderNode> {
  return apiFetch<FolderNode>(`/v1/folders/${folderId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteFolder(folderId: string): Promise<void> {
  await apiFetch<unknown>(`/v1/folders/${folderId}`, { method: 'DELETE' })
}

// ─── Documents ────────────────────────────────────────────────────────────────

export async function uploadDocument(
  folderId: string,
  formData: FormData
): Promise<Document> {
  return apiUpload<Document>(`/v1/folders/${folderId}/documents`, formData)
}

export async function searchDocuments(params: {
  folder_id?: string
  project_id?: string
  q?: string
}): Promise<Document[]> {
  const qs = new URLSearchParams()
  if (params.folder_id) qs.set('folder_id', params.folder_id)
  if (params.project_id) qs.set('project_id', params.project_id)
  if (params.q) qs.set('q', params.q)
  return apiFetch<Document[]>(`/v1/documents/search?${qs.toString()}`)
}

export async function getDocument(documentId: string): Promise<Document> {
  return apiFetch<Document>(`/v1/documents/${documentId}`)
}

export async function uploadDocumentVersion(
  documentId: string,
  formData: FormData
): Promise<Document> {
  return apiUpload<Document>(`/v1/documents/${documentId}/versions`, formData)
}

export async function getDocumentVersionDownloadUrl(
  versionId: string
): Promise<DownloadUrlResponse> {
  return apiFetch<DownloadUrlResponse>(
    `/v1/document-versions/${versionId}/download-url`
  )
}

export async function fetchConfidentialityLevels(): Promise<ReferenceLookup[]> {
  return apiFetch<ReferenceLookup[]>('/v1/confidentiality-levels')
}

export async function fetchDocumentTypes(): Promise<ReferenceLookup[]> {
  return apiFetch<ReferenceLookup[]>('/v1/document-types')
}

// ─── Archive exports ──────────────────────────────────────────────────────────

export async function createExport(projectId: string): Promise<ArchiveExport> {
  return apiFetch<ArchiveExport>(`/v1/projects/${projectId}/exports`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export async function listExports(projectId: string): Promise<ArchiveExport[]> {
  return apiFetch<ArchiveExport[]>(`/v1/projects/${projectId}/exports`)
}

export async function getExport(exportId: string): Promise<ArchiveExport> {
  return apiFetch<ArchiveExport>(`/v1/exports/${exportId}`)
}

export async function getExportDownloadUrl(
  exportId: string
): Promise<DownloadUrlResponse> {
  return apiFetch<DownloadUrlResponse>(`/v1/exports/${exportId}/download-url`)
}

export async function cancelExport(exportId: string): Promise<ArchiveExport> {
  return apiFetch<ArchiveExport>(`/v1/exports/${exportId}/cancel`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

// ─── Physical archive ─────────────────────────────────────────────────────────

export async function listRooms(): Promise<PhysicalRoom[]> {
  return apiFetch<PhysicalRoom[]>('/v1/archive/rooms')
}

export async function createRoom(
  payload: CreatePhysicalRoomPayload
): Promise<PhysicalRoom> {
  return apiFetch<PhysicalRoom>('/v1/archive/rooms', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function listLocations(roomId: string): Promise<PhysicalLocation[]> {
  return apiFetch<PhysicalLocation[]>(
    `/v1/archive/locations?room_id=${encodeURIComponent(roomId)}`
  )
}

export async function createLocation(
  payload: CreatePhysicalLocationPayload
): Promise<PhysicalLocation> {
  return apiFetch<PhysicalLocation>('/v1/archive/locations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getLocationContents(
  locationId: string
): Promise<PhysicalLocationContents> {
  return apiFetch<PhysicalLocationContents>(
    `/v1/archive/locations/${locationId}/contents`
  )
}

export async function createPhysicalFile(
  projectId: string,
  payload: CreatePhysicalFilePayload
): Promise<PhysicalFile> {
  return apiFetch<PhysicalFile>(`/v1/projects/${projectId}/physical-files`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getPhysicalFile(fileId: string): Promise<PhysicalFile> {
  return apiFetch<PhysicalFile>(`/v1/physical-files/${fileId}`)
}

export async function listProjectPhysicalFiles(projectId: string): Promise<PhysicalFile[]> {
  return apiFetch<PhysicalFile[]>(`/v1/projects/${projectId}/physical-files`)
}

export async function getPhysicalFileByQrToken(qrToken: string): Promise<PhysicalFile> {
  return apiFetch<PhysicalFile>(`/v1/physical-files/by-qr/${qrToken}`)
}

export async function checkoutPhysicalFile(
  fileId: string,
  payload: PhysicalFileCheckoutPayload
): Promise<PhysicalFile> {
  return apiFetch<PhysicalFile>(`/v1/physical-files/${fileId}/checkout`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function returnPhysicalFile(
  fileId: string,
  payload: PhysicalFileReturnPayload
): Promise<PhysicalFile> {
  return apiFetch<PhysicalFile>(`/v1/physical-files/${fileId}/return`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function movePhysicalFile(
  fileId: string,
  payload: PhysicalFileMovePayload
): Promise<PhysicalFile> {
  return apiFetch<PhysicalFile>(`/v1/physical-files/${fileId}/move`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function verifyPhysicalFile(
  fileId: string,
  payload: PhysicalFileVerifyPayload
): Promise<PhysicalFile> {
  return apiFetch<PhysicalFile>(`/v1/physical-files/${fileId}/verify`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getPhysicalFileLabel(
  fileId: string
): Promise<PhysicalFileLabel> {
  return apiFetch<PhysicalFileLabel>(`/v1/physical-files/${fileId}/label`)
}

// ─── Employees ────────────────────────────────────────────────────────────────

export async function fetchEmployees(params?: {
  status?: string
  search?: string
}): Promise<EmployeeSummary[]> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.search) qs.set('search', params.search)
  const q = qs.toString()
  return apiFetch<EmployeeSummary[]>(`/v1/employees${q ? `?${q}` : ''}`)
}

// ─── Attendance ───────────────────────────────────────────────────────────────

export async function checkIn(payload: CheckInPayload): Promise<AttendanceSession> {
  return apiFetch<AttendanceSession>('/v1/attendance/check-in', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function checkOut(payload: CheckOutPayload): Promise<AttendanceSession> {
  return apiFetch<AttendanceSession>('/v1/attendance/check-out', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchMyAttendance(params?: {
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}): Promise<AttendanceSession[]> {
  const qs = new URLSearchParams()
  if (params?.from_date) qs.set('from_date', params.from_date)
  if (params?.to_date) qs.set('to_date', params.to_date)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<AttendanceSession[]>(`/v1/attendance/me${q ? `?${q}` : ''}`)
}

export async function fetchTeamAttendance(params?: {
  employee_id?: string
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}): Promise<AttendanceSession[]> {
  const qs = new URLSearchParams()
  if (params?.employee_id) qs.set('employee_id', params.employee_id)
  if (params?.from_date) qs.set('from_date', params.from_date)
  if (params?.to_date) qs.set('to_date', params.to_date)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<AttendanceSession[]>(`/v1/attendance/team${q ? `?${q}` : ''}`)
}

export async function correctAttendanceSession(
  sessionId: string,
  payload: AttendanceCorrectionPayload
): Promise<AttendanceSession> {
  return apiFetch<AttendanceSession>(`/v1/attendance/sessions/${sessionId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function fetchDirectorAttendance(): Promise<DirectorAttendanceSummary[]> {
  return apiFetch<DirectorAttendanceSummary[]>('/v1/director/attendance')
}

// ─── Leave ────────────────────────────────────────────────────────────────────

export async function fetchLeaveTypes(): Promise<ReferenceLookup[]> {
  return apiFetch<ReferenceLookup[]>('/v1/leave-types')
}

export async function createLeaveRequest(
  payload: CreateLeaveRequestPayload
): Promise<LeaveRequest> {
  return apiFetch<LeaveRequest>('/v1/leave-requests', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchMyLeaveRequests(params?: {
  status?: string
  limit?: number
  offset?: number
}): Promise<LeaveRequest[]> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<LeaveRequest[]>(`/v1/leave-requests/me${q ? `?${q}` : ''}`)
}

export async function fetchPendingLeaveRequests(params?: {
  limit?: number
  offset?: number
}): Promise<LeaveRequest[]> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<LeaveRequest[]>(`/v1/leave-requests/pending${q ? `?${q}` : ''}`)
}

export async function approveLeaveRequest(
  requestId: string,
  payload: ReviewLeaveRequestPayload
): Promise<LeaveRequest> {
  return apiFetch<LeaveRequest>(`/v1/leave-requests/${requestId}/approve`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function rejectLeaveRequest(
  requestId: string,
  payload: ReviewLeaveRequestPayload
): Promise<LeaveRequest> {
  return apiFetch<LeaveRequest>(`/v1/leave-requests/${requestId}/reject`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function cancelLeaveRequest(requestId: string): Promise<LeaveRequest> {
  return apiFetch<LeaveRequest>(`/v1/leave-requests/${requestId}/cancel`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

// ─── Tasks ────────────────────────────────────────────────────────────────────

export async function fetchTaskStatuses(): Promise<ReferenceLookup[]> {
  return apiFetch<ReferenceLookup[]>('/v1/task-statuses')
}

export async function fetchTasks(params?: {
  project_id?: string
  assigned_to_me?: boolean
  status_code?: string
  limit?: number
  offset?: number
}): Promise<Task[]> {
  const qs = new URLSearchParams()
  if (params?.project_id) qs.set('project_id', params.project_id)
  if (params?.assigned_to_me) qs.set('assigned_to_me', 'true')
  if (params?.status_code) qs.set('status_code', params.status_code)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<Task[]>(`/v1/tasks${q ? `?${q}` : ''}`)
}

export async function createTask(payload: CreateTaskPayload): Promise<Task> {
  return apiFetch<Task>('/v1/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getTask(taskId: string): Promise<Task> {
  return apiFetch<Task>(`/v1/tasks/${taskId}`)
}

export async function updateTask(taskId: string, payload: UpdateTaskPayload): Promise<Task> {
  return apiFetch<Task>(`/v1/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function addTaskAssignees(
  taskId: string,
  payload: AddTaskAssigneesPayload
): Promise<Task> {
  return apiFetch<Task>(`/v1/tasks/${taskId}/assignees`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function addTaskComment(
  taskId: string,
  payload: AddTaskCommentPayload
): Promise<TaskComment> {
  return apiFetch<TaskComment>(`/v1/tasks/${taskId}/comments`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function linkTaskDocument(
  taskId: string,
  payload: LinkTaskDocumentPayload
): Promise<Task> {
  return apiFetch<Task>(`/v1/tasks/${taskId}/documents`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// ─── Calendar ─────────────────────────────────────────────────────────────────

export async function fetchCalendarEvents(params?: {
  from_date?: string
  to_date?: string
  project_id?: string
}): Promise<CalendarEvent[]> {
  const qs = new URLSearchParams()
  if (params?.from_date) qs.set('from_date', params.from_date)
  if (params?.to_date) qs.set('to_date', params.to_date)
  if (params?.project_id) qs.set('project_id', params.project_id)
  const q = qs.toString()
  return apiFetch<CalendarEvent[]>(`/v1/calendar/events${q ? `?${q}` : ''}`)
}

export async function createCalendarEvent(
  payload: CreateCalendarEventPayload
): Promise<CalendarEvent> {
  return apiFetch<CalendarEvent>('/v1/calendar/events', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateCalendarEvent(
  eventId: string,
  payload: UpdateCalendarEventPayload
): Promise<CalendarEvent> {
  return apiFetch<CalendarEvent>(`/v1/calendar/events/${eventId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

// ─── Director Dashboard ───────────────────────────────────────────────────────

export async function fetchDirectorOverview(): Promise<DirectorOverview> {
  return apiFetch<DirectorOverview>('/v1/director/overview')
}

export async function fetchDirectorProjects(params?: {
  limit?: number
  offset?: number
}): Promise<DirectorProject[]> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<DirectorProject[]>(`/v1/director/projects${q ? `?${q}` : ''}`)
}

export async function fetchDirectorApprovals(params?: {
  limit?: number
  offset?: number
}): Promise<DirectorApproval[]> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<DirectorApproval[]>(`/v1/director/approvals${q ? `?${q}` : ''}`)
}

export async function fetchDirectorOverdueTasks(params?: {
  limit?: number
  offset?: number
}): Promise<DirectorOverdueTask[]> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<DirectorOverdueTask[]>(`/v1/director/overdue-tasks${q ? `?${q}` : ''}`)
}

export async function fetchDirectorPhysicalFiles(params?: {
  limit?: number
  offset?: number
}): Promise<DirectorCheckedOutFile[]> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<DirectorCheckedOutFile[]>(`/v1/director/physical-files${q ? `?${q}` : ''}`)
}

export async function fetchDirectorAuditEvents(params?: {
  action_code?: string
  resource_type?: string
  limit?: number
  offset?: number
}): Promise<DirectorAuditEvent[]> {
  const qs = new URLSearchParams()
  if (params?.action_code) qs.set('action_code', params.action_code)
  if (params?.resource_type) qs.set('resource_type', params.resource_type)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const q = qs.toString()
  return apiFetch<DirectorAuditEvent[]>(`/v1/director/audit-events${q ? `?${q}` : ''}`)
}
