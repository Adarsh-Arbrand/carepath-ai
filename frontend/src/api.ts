import type { SymptomRequest, AssessmentResponse, ConfigResponse } from './types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export async function assessSymptoms(data: SymptomRequest): Promise<AssessmentResponse> {
  const response = await fetch(`${API_BASE}/assess`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Assessment failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getConfig(): Promise<ConfigResponse> {
  const response = await fetch(`${API_BASE}/config`);

  if (!response.ok) {
    throw new Error(`Failed to get config: ${response.statusText}`);
  }

  return response.json();
}
