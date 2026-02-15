export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const STORAGE_ACCESS = 'accv_access';
const STORAGE_REFRESH = 'accv_refresh';
const STORAGE_USER = 'accv_user';

export interface AuthUser {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  roles: string[];
  is_superuser: boolean;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: AuthUser;
}

export interface Control {
  id: number;
  control_code: string;
  section: string;
  standard: string;
  indicator: string;
  sort_order: number;
  active: boolean;
  status: string;
  last_evidence_date?: string | null;
  next_due_date?: string | null;
}

export interface EvidenceFile {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  uploaded_at: string;
}

export interface EvidenceItem {
  id: string;
  title: string;
  category: string;
  subtype?: string | null;
  notes?: string | null;
  event_date: string;
  valid_from?: string | null;
  valid_until?: string | null;
  created_at: string;
  files: EvidenceFile[];
}

export interface EvidenceLink {
  id: string;
  relevance_note?: string | null;
  linked_at: string;
  evidence_item: EvidenceItem;
}

export interface ControlTimeline {
  control: Control;
  evidence_items: EvidenceLink[];
}

export interface ControlStatus {
  control_id: number;
  computed_status: string;
  last_evidence_date: string | null;
  next_due_date: string | null;
  computed_at: string;
  details_json: Record<string, unknown>;
}

export interface VerificationResponse {
  verification: {
    id: string;
    control: number;
    status: 'VERIFIED' | 'REJECTED';
    remarks?: string | null;
    verified_by?: number | null;
    verified_at: string;
    evidence_snapshot_at?: string | null;
  };
  status_cache: ControlStatus;
}

export interface ExportJob {
  id: string;
  job_type: 'CONTROL_PDF' | 'SECTION_PACK' | 'FULL_PACK';
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  standard_pack: number;
  control?: number | null;
  section_code?: string | null;
  filters_json: Record<string, unknown>;
  created_by?: number | null;
  created_at: string;
  completed_at?: string | null;
  bucket: string;
  object_key: string;
  filename: string;
  size_bytes?: number | null;
  sha256?: string | null;
  error_text?: string | null;
}

export interface DashboardSummary {
  pack_version: string;
  totals: {
    total_controls: number;
    NOT_STARTED: number;
    IN_PROGRESS: number;
    READY: number;
    VERIFIED: number;
    OVERDUE: number;
    NEAR_DUE: number;
  };
  sections: Array<{
    section_code: string;
    total: number;
    READY: number;
    VERIFIED: number;
    OVERDUE: number;
  }>;
  upcoming_due: Array<{
    control_id: number;
    control_code: string;
    section_code: string;
    next_due_date: string;
  }>;
  last_computed_at: string | null;
}

export interface ComplianceAlert {
  id: string;
  control_id: number;
  control_code: string;
  alert_type: 'OVERDUE' | 'NEAR_DUE';
  triggered_at: string;
  cleared_at?: string | null;
}

export interface ControlNote {
  id: string;
  control: number;
  note_type: 'INTERNAL' | 'INSPECTION' | 'CORRECTIVE_ACTION';
  text: string;
  created_by?: number | null;
  created_by_username?: string;
  created_at: string;
  resolved: boolean;
  resolved_at?: string | null;
  resolved_by?: number | null;
  resolved_by_username?: string;
}

export interface AuditEvent {
  id: number;
  created_at: string;
  actor: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  summary: string;
}

export interface UserList {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  roles: string[];
}

// --- Auth ---

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_USER);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(STORAGE_ACCESS);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export async function login(username: string, password: string): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || err.error || `Login failed: ${response.statusText}`);
  }
  const data = await response.json();
  localStorage.setItem(STORAGE_ACCESS, data.access);
  localStorage.setItem(STORAGE_REFRESH, data.refresh);
  localStorage.setItem(STORAGE_USER, JSON.stringify(data.user));
  return data;
}

export async function refreshToken(): Promise<string> {
  const refresh = localStorage.getItem(STORAGE_REFRESH);
  if (!refresh) throw new Error('No refresh token');
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    logout();
    throw new Error('Token refresh failed');
  }
  const data = await response.json();
  localStorage.setItem(STORAGE_ACCESS, data.access);
  if (data.refresh) {
    localStorage.setItem(STORAGE_REFRESH, data.refresh);
  }
  return data.access;
}

export async function getMe(): Promise<AuthUser> {
  const user = await authFetch(`${API_BASE_URL}/auth/me`).then((r) => r.json());
  localStorage.setItem(STORAGE_USER, JSON.stringify(user));
  return user;
}

export function logout(): void {
  localStorage.removeItem(STORAGE_ACCESS);
  localStorage.removeItem(STORAGE_REFRESH);
  localStorage.removeItem(STORAGE_USER);
}

// --- Auth-aware fetch ---

async function authFetch(
  url: string,
  options: RequestInit = {},
  retried = false
): Promise<Response> {
  const access = getAccessToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  if (access) {
    headers['Authorization'] = `Bearer ${access}`;
  }
  if (headers['Content-Type'] === undefined && options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 && !retried && access) {
    try {
      const newAccess = await refreshToken();
      return authFetch(
        url,
        {
          ...options,
          headers: {
            ...((options.headers as Record<string, string>) || {}),
            Authorization: `Bearer ${newAccess}`,
          },
        },
        true
      );
    } catch {
      logout();
      return response;
    }
  }

  return response;
}

async function checkOk(response: Response): Promise<void> {
  if (!response.ok) {
    let msg = response.statusText;
    try {
      const err = await response.json();
      if (err.detail) msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
    } catch {
      /* ignore */
    }
    if (response.status === 403) msg = msg || 'You do not have permission to perform this action.';
    throw new Error(msg);
  }
}

// --- API methods (all use authFetch) ---

export const api = {
  async getControls(params?: { section?: string; q?: string }): Promise<Control[]> {
    const queryParams = new URLSearchParams();
    if (params?.section) queryParams.append('section', params.section);
    if (params?.q) queryParams.append('q', params.q);
    const url = `${API_BASE_URL}/controls/?${queryParams.toString()}`;
    const response = await authFetch(url);
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    const data = await response.json();
    return data.results || data;
  },

  async getControlTimeline(controlId: number): Promise<ControlTimeline> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/timeline`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async getControlStatus(controlId: number): Promise<ControlStatus> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/status`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async verifyControl(controlId: number, remarks?: string): Promise<VerificationResponse> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ remarks }),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async rejectControl(controlId: number, remarks?: string): Promise<VerificationResponse> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ remarks }),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async createControlExport(controlId: number): Promise<{ job: ExportJob; download: { url: string; expires_in: number } }> {
    const response = await authFetch(`${API_BASE_URL}/exports/control/${controlId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async createSectionExport(sectionCode: string): Promise<{ job: ExportJob; download: { url: string; expires_in: number } }> {
    const response = await authFetch(`${API_BASE_URL}/exports/section/${sectionCode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async createFullExport(): Promise<{ job: ExportJob; download: { url: string; expires_in: number } }> {
    const response = await authFetch(`${API_BASE_URL}/exports/full`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async downloadExport(jobId: string): Promise<{ url: string; expires_in: number }> {
    const response = await authFetch(`${API_BASE_URL}/exports/${jobId}/download`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async listControlExports(controlId: number): Promise<ExportJob[]> {
    const response = await authFetch(`${API_BASE_URL}/exports/control/${controlId}`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await authFetch(`${API_BASE_URL}/dashboard/summary`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async getAlerts(): Promise<ComplianceAlert[]> {
    const response = await authFetch(`${API_BASE_URL}/alerts`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async getControlNotes(controlId: number): Promise<ControlNote[]> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/notes`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async createControlNote(controlId: number, payload: { note_type: string; text: string }): Promise<ControlNote> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async updateControlNote(controlId: number, noteId: string, payload: Partial<{ note_type: string; text: string; resolved: boolean }>): Promise<ControlNote> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/notes/${noteId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async deleteControlNote(controlId: number, noteId: string): Promise<void> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/notes/${noteId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  },

  async createEvidenceItem(payload: {
    title: string;
    category: string;
    event_date: string;
    notes?: string;
    subtype?: string;
    valid_from?: string;
    valid_until?: string;
  }): Promise<EvidenceItem> {
    const response = await authFetch(`${API_BASE_URL}/evidence-items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async uploadEvidenceFiles(evidenceItemId: string, files: File[]): Promise<{ files: EvidenceFile[] }> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await authFetch(`${API_BASE_URL}/evidence-items/${evidenceItemId}/files`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async linkEvidenceToControl(controlId: number, evidenceItemId: string, note?: string): Promise<EvidenceLink> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/link-evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ evidence_item_id: evidenceItemId, note }),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async unlinkEvidenceFromControl(controlId: number, linkId: string): Promise<void> {
    const response = await authFetch(`${API_BASE_URL}/controls/${controlId}/unlink-evidence/${linkId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  },

  async downloadEvidenceFile(fileId: string): Promise<{ url: string; expires_in: number }> {
    const response = await authFetch(`${API_BASE_URL}/evidence-files/${fileId}/download`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async healthCheck(): Promise<unknown> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },

  // Users (ADMIN only)
  async getUsers(): Promise<UserList[]> {
    const response = await authFetch(`${API_BASE_URL}/users`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async createUser(payload: { username: string; password: string; first_name?: string; last_name?: string; roles?: string[] }): Promise<UserList> {
    const response = await authFetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async updateUser(userId: number, payload: Partial<{ first_name: string; last_name: string; is_active: boolean; roles: string[] }>): Promise<UserList> {
    const response = await authFetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },

  async resetUserPassword(userId: number, password: string): Promise<void> {
    const response = await authFetch(`${API_BASE_URL}/users/${userId}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  },

  // Audit (ADMIN/MANAGER/AUDITOR)
  async getAuditEvents(params?: { action?: string; entity_type?: string; after?: string; before?: string; q?: string }): Promise<AuditEvent[]> {
    const sp = new URLSearchParams();
    if (params?.action) sp.append('action', params.action);
    if (params?.entity_type) sp.append('entity_type', params.entity_type);
    if (params?.after) sp.append('after', params.after);
    if (params?.before) sp.append('before', params.before);
    if (params?.q) sp.append('q', params.q);
    const qs = sp.toString();
    const url = `${API_BASE_URL}/audit/events${qs ? `?${qs}` : ''}`;
    const response = await authFetch(url);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
  },
};
