export type AgeGroup = '0-2' | '3-12' | '13-17' | '18-64' | '65+';
export type UrgencyLevel = 'emergency' | 'urgent' | 'routine' | 'unknown';

export interface SymptomRequest {
  age_group: AgeGroup;
  main_symptom: string;
  duration: string;
  onset: string;
  severity: string;
  associated_symptoms: string[];
  warning_signs: string[];
  additional_context?: string;
}

export interface WarningSign {
  sign: string;
  description: string;
  source: string;
}

export interface AssessmentResponse {
  urgency: UrgencyLevel;
  warning_signs_detected: WarningSign[];
  reasoning: string;
  recommended_next_steps: string[];
  limitations: string[];
  is_demo_mode: boolean;
  needs_follow_up: boolean;
  follow_up_question?: string;
}

export interface ConfigResponse {
  ai_enabled: boolean;
  demo_mode: boolean;
}
