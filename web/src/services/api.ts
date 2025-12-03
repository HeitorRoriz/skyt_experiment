// API Service for SKYT
// Uses environment variable for API URL, falls back to relative path for same-origin
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

// Types
export interface Contract {
  id: string;
  version: string;
  task_intent: string;
  algorithm_family: string;
  test_count: number;
}

export interface RestrictionPreset {
  id: string;
  name: string;
  version: string;
  source: string;
  authority: string | null;
  rule_count: number;
}

export interface JobRequest {
  contract_id: string;
  num_runs: number;
  temperature: number;
  model: string;
  restriction_ids: string[];
}

export interface Job {
  job_id: string;
  status: string;
  contract_id: string;
  num_runs: number;
  temperature: number;
  created_at: string;
  metrics?: {
    R_raw: number;
    R_anchor_pre: number;
    R_anchor_post: number;
    Delta_rescue: number;
    R_behavioral: number;
    R_structural: number;
  };
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Auth state
let authToken: string | null = localStorage.getItem('skyt_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('skyt_token', token);
  } else {
    localStorage.removeItem('skyt_token');
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

// API calls
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// Auth
export async function login(email: string, password: string): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await fetch(`${API_BASE}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Invalid credentials');
  }
  
  const data = await response.json();
  setAuthToken(data.access_token);
  return data;
}

export function logout() {
  setAuthToken(null);
}

// Contracts
export async function getContracts(): Promise<Contract[]> {
  return fetchApi<Contract[]>('/contracts');
}

export async function getContract(id: string): Promise<Contract> {
  return fetchApi<Contract>(`/contracts/${id}`);
}

// Restrictions
export async function getRestrictionPresets(): Promise<RestrictionPreset[]> {
  return fetchApi<RestrictionPreset[]>('/restrictions/presets');
}

// Jobs
export async function submitJob(request: JobRequest): Promise<{ job_id: string; status: string }> {
  return fetchApi('/pipeline/run', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getJob(jobId: string): Promise<Job> {
  return fetchApi<Job>(`/jobs/${jobId}`);
}

export async function getJobs(): Promise<Job[]> {
  return fetchApi<Job[]>('/pipeline/jobs');
}

// Job Progress
export interface JobProgress {
  job_id: string;
  phase: string;
  completed_runs: number;
  total_runs: number;
  progress_percent: number;
  current_run_status: string;
  estimated_completion: string | null;
}

export async function getJobProgress(jobId: string): Promise<JobProgress> {
  return fetchApi<JobProgress>(`/jobs/${jobId}/progress`);
}

// Cancel Job
export interface CancelResponse {
  job_id: string;
  status: string;
  message: string;
}

export async function cancelJob(jobId: string): Promise<CancelResponse> {
  return fetchApi<CancelResponse>(`/jobs/${jobId}/cancel`, {
    method: 'POST',
  });
}

// WebSocket for real-time job updates
export function subscribeToJob(
  jobId: string,
  onProgress: (progress: JobProgress) => void,
  onError?: (error: Error) => void
): () => void {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/jobs/${jobId}/stream`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onProgress(data);
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };
  
  ws.onerror = () => {
    if (onError) {
      onError(new Error('WebSocket error'));
    }
  };
  
  ws.onclose = () => {
    console.log('WebSocket closed');
  };
  
  // Return cleanup function
  return () => {
    ws.close();
  };
}

// Health
export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch('/health');
  return response.json();
}
