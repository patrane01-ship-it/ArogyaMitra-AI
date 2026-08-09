import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config();

export const PORT = 3000;
export const HOST = '0.0.0.0';

export const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';
export const SECRET_KEY = process.env.SECRET_KEY || 'arogya_mitra_secret_key_123';
export const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'arogya_mitra_enc_key_32bytes_default'; // In prod, should be 32 bytes base64
export const SQLITE_DB_PATH = process.env.SQLITE_DB_PATH || path.join(process.cwd(), 'backend', 'data', 'arogya_mitra.db');
export const UPLOAD_DIR = process.env.UPLOAD_DIR || path.join(process.cwd(), 'backend', 'data', 'records', 'encrypted');
export const CHROMA_DB_PATH = process.env.CHROMA_DB_PATH || path.join(process.cwd(), 'backend', 'data', 'chroma_db');

export const SUPPORTED_PARAMETERS = [
  'HbA1c',
  'Fasting Blood Sugar',
  'Total Cholesterol',
  'LDL',
  'HDL',
  'Triglycerides',
  'Hemoglobin',
  'Creatinine',
  'eGFR',
  'Blood Pressure Systolic',
  'Blood Pressure Diastolic',
  'TSH',
  'Vitamin D',
  'Vitamin B12',
  'Uric Acid'
];

export interface ParameterRange {
  min: number;
  max: number;
  unit: string;
}

export const PARAM_REFERENCE_RANGES: Record<string, ParameterRange> = {
  'HbA1c': { min: 4.0, max: 5.6, unit: '%' },
  'Fasting Blood Sugar': { min: 70, max: 100, unit: 'mg/dL' },
  'Total Cholesterol': { min: 100, max: 200, unit: 'mg/dL' },
  'LDL': { min: 0, max: 100, unit: 'mg/dL' },
  'HDL': { min: 40, max: 60, unit: 'mg/dL' },
  'Triglycerides': { min: 0, max: 150, unit: 'mg/dL' },
  'Hemoglobin': { min: 12.0, max: 17.5, unit: 'g/dL' },
  'Creatinine': { min: 0.6, max: 1.2, unit: 'mg/dL' },
  'eGFR': { min: 90, max: 150, unit: 'mL/min/1.73m2' },
  'Blood Pressure Systolic': { min: 90, max: 120, unit: 'mmHg' },
  'Blood Pressure Diastolic': { min: 60, max: 80, unit: 'mmHg' },
  'TSH': { min: 0.4, max: 4.0, unit: 'mIU/L' },
  'Vitamin D': { min: 30, max: 100, unit: 'ng/mL' },
  'Vitamin B12': { min: 200, max: 900, unit: 'pg/mL' },
  'Uric Acid': { min: 3.5, max: 7.2, unit: 'mg/dL' }
};
