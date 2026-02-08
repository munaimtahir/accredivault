export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface Control {
  id: number;
  control_code: string;
  section: string;
  indicator: string;
  sort_order: number;
  active: boolean;
  status: string;
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
  
  async healthCheck(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }
};
