export type RecordType = 'LAB_REPORT' | 'PRESCRIPTION' | 'DOCTOR_NOTE' | 'IMAGING' | 'MANUAL_ENTRY';
export type ParameterStatus = 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL';
export type ReminderType = 'MEDICATION' | 'TEST_DUE' | 'DOCTOR_VISIT' | 'REFILL';
export type RecurrenceType = 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export interface HealthRecord {
  record_id: string;
  user_id: string;
  record_type: RecordType;
  upload_date: string;
  report_date: string;
  source_file_path: string | null;
  raw_text: string | null;
  extracted_entities: Record<string, number>;
  encryption_hash: string | null;
  is_processed: boolean;
  share_token: string | null;
  share_expires_at: string | null;
}

export interface ClinicalParameter {
  param_id: string;
  record_id: string;
  param_name: string;
  value: number;
  unit: string;
  reference_range_min: number | null;
  reference_range_max: number | null;
  report_date: string;
  status: ParameterStatus;
  anomaly_score: number | null;
}

export interface ContributingFactor {
  param_name: string;
  value: number;
  weight: number;
  contribution: number;
  status: ParameterStatus;
}

export interface RiskScore {
  score_id: string;
  user_id: string;
  computed_at: string;
  overall_risk: number;
  risk_level: RiskLevel;
  contributing_factors: ContributingFactor[];
  recommendations: string[];
  version: number;
}

export interface Reminder {
  reminder_id: string;
  user_id: string;
  reminder_type: ReminderType;
  title: string;
  due_date: string;
  recurrence: RecurrenceType;
  is_active: boolean;
  is_acknowledged: boolean;
  created_from_record_id: string | null;
}

export interface DoctorReport {
  report_id: string;
  user_id: string;
  generated_at: string;
  report_content: string;
  pdf_path: string | null;
  records_included: string[];
  share_token: string | null;
  share_expires_at: string | null;
}
