import { 
  HealthRecord, 
  ClinicalParameter, 
  Reminder, 
  RiskScore, 
  DoctorReport,
  RecordType,
  ReminderType,
  RecurrenceType
} from '../types.ts';

const API_BASE = '/api';

export class ApiError extends Error {
  status: number;
  errorName: string;

  constructor(message: string, status: number, errorName: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorName = errorName;
  }
}

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(url, options);
  
  if (!res.ok) {
    let errorData: any = {};
    try {
      errorData = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(
      errorData.message || `API error with status ${res.status}`,
      res.status,
      errorData.error || 'UnknownError'
    );
  }

  return res.json() as Promise<T>;
}

export const api = {
  // HEALTH RECORDS
  async getRecords(): Promise<HealthRecord[]> {
    return fetchJson<HealthRecord[]>(`${API_BASE}/records`);
  },

  async getRecord(id: string): Promise<HealthRecord> {
    return fetchJson<HealthRecord>(`${API_BASE}/records/${id}`);
  },

  async uploadRecord(
    file: File | null, 
    recordType: RecordType, 
    reportDate: string, 
    rawText?: string
  ): Promise<HealthRecord> {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    formData.append('record_type', recordType);
    formData.append('report_date', reportDate);
    if (rawText) {
      formData.append('raw_text', rawText);
    }

    const res = await fetch(`${API_BASE}/records/upload`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      let errorData: any = {};
      try {
        errorData = await res.json();
      } catch {
        // ignore
      }
      throw new ApiError(
        errorData.message || `Upload failed with status ${res.status}`,
        res.status,
        errorData.error || 'UploadError'
      );
    }

    return res.json() as Promise<HealthRecord>;
  },

  async updateRecord(id: string, record_type?: RecordType, report_date?: string): Promise<HealthRecord> {
    return fetchJson<HealthRecord>(`${API_BASE}/records/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ record_type, report_date })
    });
  },

  async deleteRecord(id: string): Promise<{ success: boolean; message: string }> {
    return fetchJson<{ success: boolean; message: string }>(`${API_BASE}/records/${id}`, {
      method: 'DELETE'
    });
  },

  // CLINICAL PARAMETERS
  async getParameters(): Promise<ClinicalParameter[]> {
    return fetchJson<ClinicalParameter[]>(`${API_BASE}/params`);
  },

  async getParameterHistory(paramName: string): Promise<ClinicalParameter[]> {
    return fetchJson<ClinicalParameter[]>(`${API_BASE}/params/${encodeURIComponent(paramName)}`);
  },

  async updateParameter(paramId: string, value: number): Promise<ClinicalParameter> {
    return fetchJson<ClinicalParameter>(`${API_BASE}/params/${paramId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value })
    });
  },

  // REMINDERS
  async getReminders(activeOnly: boolean = false): Promise<Reminder[]> {
    const query = activeOnly ? '?active_only=true' : '';
    return fetchJson<Reminder[]>(`${API_BASE}/reminders${query}`);
  },

  async createReminder(reminder: {
    title: string;
    reminder_type: ReminderType;
    due_date: string;
    recurrence: RecurrenceType;
  }): Promise<Reminder> {
    return fetchJson<Reminder>(`${API_BASE}/reminders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reminder)
    });
  },

  async updateReminder(id: string, updates: {
    title?: string;
    reminder_type?: ReminderType;
    due_date?: string;
    recurrence?: RecurrenceType;
    is_active?: boolean;
  }): Promise<Reminder> {
    return fetchJson<Reminder>(`${API_BASE}/reminders/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
  },

  async deleteReminder(id: string): Promise<{ success: boolean; message: string }> {
    return fetchJson<{ success: boolean; message: string }>(`${API_BASE}/reminders/${id}`, {
      method: 'DELETE'
    });
  },

  async acknowledgeReminder(id: string, is_acknowledged: boolean = true): Promise<Reminder> {
    return fetchJson<Reminder>(`${API_BASE}/reminders/${id}/ack`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_acknowledged })
    });
  },

  // DOCTOR REPORTS
  async getLatestDoctorReport(): Promise<DoctorReport> {
    return fetchJson<DoctorReport>(`${API_BASE}/report/latest`);
  },

  async generateDoctorReport(): Promise<DoctorReport> {
    return fetchJson<DoctorReport>(`${API_BASE}/report/generate`, {
      method: 'POST'
    });
  },

  async createShareLink(reportId: string, expiryHours: number = 24): Promise<{
    share_token: string;
    share_url: string;
    expires_at: string;
  }> {
    return fetchJson<{
      share_token: string;
      share_url: string;
      expires_at: string;
    }>(`${API_BASE}/report/${reportId}/share`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expiry_hours: expiryHours })
    });
  },

  // RISK ENGINE
  async getLatestRiskScore(): Promise<RiskScore> {
    return fetchJson<RiskScore>(`${API_BASE}/risk/current`);
  },

  async getRiskHistory(): Promise<RiskScore[]> {
    return fetchJson<RiskScore[]>(`${API_BASE}/risk/history`);
  },

  async recomputeRiskScore(): Promise<RiskScore> {
    return fetchJson<RiskScore>(`${API_BASE}/risk/recompute`, {
      method: 'POST'
    });
  },

  // PUBLIC SHARED LINKS
  async getSharedContent(token: string): Promise<{
    type: 'DOCTOR_REPORT' | 'HEALTH_RECORD';
    data: any;
    clinical_parameters?: ClinicalParameter[];
  }> {
    return fetchJson<{
      type: 'DOCTOR_REPORT' | 'HEALTH_RECORD';
      data: any;
      clinical_parameters?: ClinicalParameter[];
    }>(`${API_BASE}/share/${token}`);
  },

  // AI COMPANION CHAT
  async sendChatMessage(message: string, history: { role: 'user' | 'model'; text: string }[]): Promise<{
    text: string;
    sources?: { title: string; uri: string }[];
  }> {
    return fetchJson<{
      text: string;
      sources?: { title: string; uri: string }[];
    }>(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history })
    });
  }
};
