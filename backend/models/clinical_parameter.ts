import crypto from 'crypto';
import { 
  InvalidParameterValueError, 
  MissingUnitError 
} from '../exceptions/arogya_errors.ts';
import { PARAM_REFERENCE_RANGES, SUPPORTED_PARAMETERS } from '../config.ts';

export type ParameterStatus = 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL';

export class ClinicalParameter {
  param_id: string;
  record_id: string;
  param_name: string;
  value: number;
  unit: string;
  reference_range_min: number | null;
  reference_range_max: number | null;
  report_date: Date;
  status: ParameterStatus;
  anomaly_score: number | null;

  constructor(params: {
    param_id?: string;
    record_id: string;
    param_name: string;
    value: number;
    unit: string;
    reference_range_min?: number | null;
    reference_range_max?: number | null;
    report_date: Date;
    status?: ParameterStatus;
    anomaly_score?: number | null;
  }) {
    this.param_id = params.param_id || globalThis.crypto?.randomUUID() || crypto.randomUUID();
    this.record_id = params.record_id;
    this.param_name = params.param_name;
    this.value = params.value;
    this.unit = params.unit;
    
    // Attempt to load default ranges from config if not provided
    const defaults = PARAM_REFERENCE_RANGES[params.param_name];
    this.reference_range_min = params.reference_range_min !== undefined ? params.reference_range_min : (defaults ? defaults.min : null);
    this.reference_range_max = params.reference_range_max !== undefined ? params.reference_range_max : (defaults ? defaults.max : null);
    
    this.report_date = params.report_date;
    this.anomaly_score = params.anomaly_score || null;
    this.status = params.status || 'NORMAL';
  }

  computeStatus(): ParameterStatus {
    const min = this.reference_range_min;
    const max = this.reference_range_max;

    if (min === null || max === null) {
      return 'NORMAL'; // Fallback if no reference ranges exist
    }

    // Critical check: if value is extremely elevated, e.g., double the upper limit
    if (this.value > max * 2) {
      return 'CRITICAL';
    }

    if (this.value < min) {
      return 'LOW';
    }

    if (this.value > max) {
      return 'HIGH';
    }

    return 'NORMAL';
  }

  validate(): void {
    if (typeof this.value !== 'number' || isNaN(this.value) || this.value <= 0) {
      throw new InvalidParameterValueError(`value must be a positive number. Got: ${this.value}`);
    }

    if (!this.unit || this.unit.trim() === '') {
      throw new MissingUnitError('unit must not be empty');
    }

    if (!SUPPORTED_PARAMETERS.includes(this.param_name)) {
      // Just log warning or validate gently. Let's make sure it's valid.
    }

    // Auto-compute status
    this.status = this.computeStatus();
  }

  toDict(): Record<string, any> {
    return {
      param_id: this.param_id,
      record_id: this.record_id,
      param_name: this.param_name,
      value: this.value,
      unit: this.unit,
      reference_range_min: this.reference_range_min,
      reference_range_max: this.reference_range_max,
      report_date: this.report_date.toISOString(),
      status: this.status,
      anomaly_score: this.anomaly_score
    };
  }

  static fromDict(data: Record<string, any>): ClinicalParameter {
    return new ClinicalParameter({
      param_id: data.param_id,
      record_id: data.record_id,
      param_name: data.param_name,
      value: Number(data.value),
      unit: data.unit,
      reference_range_min: data.reference_range_min !== null ? Number(data.reference_range_min) : null,
      reference_range_max: data.reference_range_max !== null ? Number(data.reference_range_max) : null,
      report_date: new Date(data.report_date),
      status: data.status as ParameterStatus,
      anomaly_score: data.anomaly_score !== null ? Number(data.anomaly_score) : null
    });
  }
}
