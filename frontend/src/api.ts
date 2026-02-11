export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface Control {
  id: number;
  control_code: string;
  section: string;
  standard: string;
  indicator: string;
  sort_order: number;
  active: boolean;
  status: string;
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

export const api = {
  async getControls(params?: { section?: string; q?: string }): Promise<Control[]> {
    const queryParams = new URLSearchParams();
    if (params?.section) queryParams.append('section', params.section);
    if (params?.q) queryParams.append('q', params.q);

    const url = `${API_BASE_URL}/controls/?${queryParams.toString()}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    // Handle both paginated and non-paginated responses
    return data.results || data;
  },

  async getControlTimeline(controlId: number): Promise<ControlTimeline> {
    const response = await fetch(`${API_BASE_URL}/controls/${controlId}/timeline`);
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
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
    const response = await fetch(`${API_BASE_URL}/evidence-items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  },

  async uploadEvidenceFiles(evidenceItemId: string, files: File[]): Promise<{ files: EvidenceFile[] }> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await fetch(`${API_BASE_URL}/evidence-items/${evidenceItemId}/files`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  },

  async linkEvidenceToControl(controlId: number, evidenceItemId: string, note?: string): Promise<EvidenceLink> {
    const response = await fetch(`${API_BASE_URL}/controls/${controlId}/link-evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ evidence_item_id: evidenceItemId, note }),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  },

  async downloadEvidenceFile(fileId: string): Promise<{ url: string; expires_in: number }> {
    const response = await fetch(`${API_BASE_URL}/evidence-files/${fileId}/download`);
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  },

  async healthCheck(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }
};
