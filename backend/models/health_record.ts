import crypto from 'crypto'; // We will use node's crypto for generating UUIDs and share tokens
import { 
  InvalidRecordTypeError, 
  FutureDateError, 
  OCRExtractionError 
} from '../exceptions/arogya_errors.ts';

export type RecordType = 'LAB_REPORT' | 'PRESCRIPTION' | 'DOCTOR_NOTE' | 'IMAGING' | 'MANUAL_ENTRY';

export class HealthRecord {
  record_id: string;
  user_id: string;
  record_type: RecordType;
  upload_date: Date;
  report_date: Date;
  source_file_path: string | null;
  raw_text: string | null;
  extracted_entities: Record<string, any>;
  encryption_hash: string | null;
  is_processed: boolean;
  is_deleted: boolean;
  share_token: string | null;
  share_expires_at: Date | null;

  constructor(params: {
    record_id?: string;
    user_id?: string;
    record_type: RecordType;
    upload_date?: Date;
    report_date: Date;
    source_file_path?: string | null;
    raw_text?: string | null;
    extracted_entities?: Record<string, any>;
    encryption_hash?: string | null;
    is_processed?: boolean;
    is_deleted?: boolean;
    share_token?: string | null;
    share_expires_at?: Date | null;
  }) {
    this.record_id = params.record_id || globalThis.crypto?.randomUUID() || crypto.randomUUID();
    this.user_id = params.user_id || 'local_user';
    this.record_type = params.record_type;
    this.upload_date = params.upload_date || new Date();
    this.report_date = params.report_date;
    this.source_file_path = params.source_file_path || null;
    this.raw_text = params.raw_text || null;
    this.extracted_entities = params.extracted_entities || {};
    this.encryption_hash = params.encryption_hash || null;
    this.is_processed = params.is_processed || false;
    this.is_deleted = params.is_deleted || false;
    this.share_token = params.share_token || null;
    this.share_expires_at = params.share_expires_at || null;
  }

  validate(): void {
    const validTypes: RecordType[] = ['LAB_REPORT', 'PRESCRIPTION', 'DOCTOR_NOTE', 'IMAGING', 'MANUAL_ENTRY'];
    if (!validTypes.includes(this.record_type)) {
      throw new InvalidRecordTypeError(
        `record_type must be one of LAB_REPORT, PRESCRIPTION, DOCTOR_NOTE, IMAGING, MANUAL_ENTRY. Got: ${this.record_type}`
      );
    }

    const now = new Date();
    // Allow a small grace period for timezone differences (e.g., 5 seconds)
    if (this.report_date.getTime() > now.getTime() + 5000) {
      throw new FutureDateError(`report_date cannot be in the future. Got: ${this.report_date.toISOString()}`);
    }

    if (this.is_processed && (!this.raw_text || this.raw_text.trim() === '')) {
      throw new OCRExtractionError('raw_text cannot be empty after processing');
    }
  }

  toDict(): Record<string, any> {
    return {
      record_id: this.record_id,
      user_id: this.user_id,
      record_type: this.record_type,
      upload_date: this.upload_date.toISOString(),
      report_date: this.report_date.toISOString(),
      source_file_path: this.source_file_path,
      raw_text: this.raw_text,
      extracted_entities: this.extracted_entities,
      encryption_hash: this.encryption_hash,
      is_processed: this.is_processed ? 1 : 0,
      is_deleted: this.is_deleted ? 1 : 0,
      share_token: this.share_token,
      share_expires_at: this.share_expires_at ? this.share_expires_at.toISOString() : null
    };
  }

  static fromDict(data: Record<string, any>): HealthRecord {
    return new HealthRecord({
      record_id: data.record_id,
      user_id: data.user_id,
      record_type: data.record_type as RecordType,
      upload_date: new Date(data.upload_date),
      report_date: new Date(data.report_date),
      source_file_path: data.source_file_path,
      raw_text: data.raw_text,
      extracted_entities: typeof data.extracted_entities === 'string' 
        ? JSON.parse(data.extracted_entities) 
        : data.extracted_entities || {},
      encryption_hash: data.encryption_hash,
      is_processed: !!data.is_processed,
      is_deleted: !!data.is_deleted,
      share_token: data.share_token,
      share_expires_at: data.share_expires_at ? new Date(data.share_expires_at) : null
    });
  }

  generateShareToken(expiryHours: number = 24): string {
    this.share_token = crypto.randomBytes(16).toString('hex');
    const expires = new Date();
    expires.setHours(expires.getHours() + expiryHours);
    this.share_expires_at = expires;
    return this.share_token;
  }

  isShareValid(): boolean {
    if (!this.share_token || !this.share_expires_at) {
      return false;
    }
    const now = new Date();
    return now.getTime() < this.share_expires_at.getTime();
  }
}
