import crypto from 'crypto';
import { InsufficientDataError } from '../exceptions/arogya_errors.ts';

export class DoctorReport {
  report_id: string;
  user_id: string;
  generated_at: Date;
  report_content: string;
  pdf_path: string | null;
  records_included: string[];
  share_token: string | null;
  share_expires_at: Date | null;
  share_generated_at: Date | null;

  constructor(params: {
    report_id?: string;
    user_id?: string;
    generated_at?: Date;
    report_content: string;
    pdf_path?: string | null;
    records_included: string[];
    share_token?: string | null;
    share_expires_at?: Date | null;
    share_generated_at?: Date | null;
  }) {
    this.report_id = params.report_id || globalThis.crypto?.randomUUID() || crypto.randomUUID();
    this.user_id = params.user_id || 'local_user';
    this.generated_at = params.generated_at || new Date();
    this.report_content = params.report_content;
    this.pdf_path = params.pdf_path || null;
    this.records_included = params.records_included || [];
    this.share_token = params.share_token || null;
    this.share_expires_at = params.share_expires_at || null;
    this.share_generated_at = params.share_generated_at || null;
  }

  validate(): void {
    if (!this.report_content || this.report_content.trim() === '') {
      throw new InsufficientDataError('Report content cannot be empty.');
    }

    if (!this.records_included || this.records_included.length === 0) {
      throw new InsufficientDataError('Doctor report must include at least 1 health record.');
    }
  }

  generateShareToken(expiryHours: number = 24): string {
    this.share_token = crypto.randomBytes(16).toString('hex');
    const expires = new Date();
    expires.setHours(expires.getHours() + expiryHours);
    this.share_expires_at = expires;
    this.share_generated_at = new Date();
    return this.share_token;
  }

  isShareValid(): boolean {
    if (!this.share_token || !this.share_expires_at) {
      return false;
    }
    const now = new Date();
    return now.getTime() < this.share_expires_at.getTime();
  }

  toDict(): Record<string, any> {
    return {
      report_id: this.report_id,
      user_id: this.user_id,
      generated_at: this.generated_at.toISOString(),
      report_content: this.report_content,
      pdf_path: this.pdf_path,
      records_included: this.records_included,
      share_token: this.share_token,
      share_expires_at: this.share_expires_at ? this.share_expires_at.toISOString() : null,
      share_generated_at: this.share_generated_at ? this.share_generated_at.toISOString() : null
    };
  }

  static fromDict(data: Record<string, any>): DoctorReport {
    return new DoctorReport({
      report_id: data.report_id,
      user_id: data.user_id,
      generated_at: new Date(data.generated_at),
      report_content: data.report_content,
      pdf_path: data.pdf_path,
      records_included: typeof data.records_included === 'string'
        ? JSON.parse(data.records_included)
        : data.records_included || [],
      share_token: data.share_token,
      share_expires_at: data.share_expires_at ? new Date(data.share_expires_at) : null,
      share_generated_at: data.share_generated_at ? new Date(data.share_generated_at) : null
    });
  }
}
