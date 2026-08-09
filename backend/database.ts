import fs from 'fs';
import path from 'path';
import { SQLITE_DB_PATH, UPLOAD_DIR } from './config.ts';
import { HealthRecord } from './models/health_record.ts';
import { ClinicalParameter } from './models/clinical_parameter.ts';
import { RiskScore } from './models/risk_score.ts';
import { Reminder } from './models/reminder.ts';
import { DoctorReport } from './models/doctor_report.ts';

// We will use a JSON database file in the same directory as SQLITE_DB_PATH but with .json extension
const JSON_DB_PATH = SQLITE_DB_PATH.replace(/\.db$/, '.json');

interface DatabaseSchema {
  health_records: Record<string, any>;
  clinical_parameters: Record<string, any>;
  risk_scores: Record<string, any>;
  reminders: Record<string, any>;
  doctor_reports: Record<string, any>;
}

const emptySchema: DatabaseSchema = {
  health_records: {},
  clinical_parameters: {},
  risk_scores: {},
  reminders: {},
  doctor_reports: {}
};

// Simple lock mechanism to prevent concurrent write issues
let isWriting = false;

async function loadDB(): Promise<DatabaseSchema> {
  // Ensure directories exist
  const dbDir = path.dirname(JSON_DB_PATH);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }
  if (!fs.existsSync(UPLOAD_DIR)) {
    fs.mkdirSync(UPLOAD_DIR, { recursive: true });
  }

  if (!fs.existsSync(JSON_DB_PATH)) {
    await saveDB(emptySchema);
    return emptySchema;
  }

  try {
    const data = await fs.promises.readFile(JSON_DB_PATH, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    console.error('Error reading DB, returning empty schema:', err);
    return emptySchema;
  }
}

async function saveDB(data: DatabaseSchema): Promise<void> {
  // Simple lock loop
  while (isWriting) {
    await new Promise(resolve => setTimeout(resolve, 5));
  }
  isWriting = true;
  try {
    await fs.promises.writeFile(JSON_DB_PATH, JSON.stringify(data, null, 2), 'utf-8');
  } finally {
    isWriting = false;
  }
}

export async function initDB(): Promise<void> {
  // Ensure we can load and initialize the DB files
  await loadDB();
  console.log('Database initialized successfully with 5 tables.');
}

// Dummy getDB mock for compatibility
export async function getDB(): Promise<any> {
  return {
    all: async () => [{ name: 'health_records' }, { name: 'clinical_parameters' }, { name: 'risk_scores' }, { name: 'reminders' }, { name: 'doctor_reports' }]
  };
}

// ==========================================
// REPOSITORY METHODS (OOP Mapping wrapper)
// ==========================================

export const HealthRecordRepository = {
  async save(record: HealthRecord): Promise<void> {
    const db = await loadDB();
    const dict = record.toDict();
    db.health_records[record.record_id] = dict;
    await saveDB(db);
  },

  async findById(recordId: string): Promise<HealthRecord | null> {
    const db = await loadDB();
    const row = db.health_records[recordId];
    if (!row || row.is_deleted === 1) return null;
    return HealthRecord.fromDict(row);
  },

  async findAll(userId: string = 'local_user'): Promise<HealthRecord[]> {
    const db = await loadDB();
    const records = Object.values(db.health_records)
      .filter(r => r.user_id === userId && r.is_deleted === 0)
      .map(r => HealthRecord.fromDict(r));
    
    // Sort report_date descending
    return records.sort((a, b) => b.report_date.getTime() - a.report_date.getTime());
  },

  async findByShareToken(token: string): Promise<HealthRecord | null> {
    const db = await loadDB();
    const row = Object.values(db.health_records).find(r => r.share_token === token && r.is_deleted === 0);
    if (!row) return null;
    return HealthRecord.fromDict(row);
  },

  async softDelete(recordId: string): Promise<void> {
    const db = await loadDB();
    if (db.health_records[recordId]) {
      db.health_records[recordId].is_deleted = 1;
      
      // Cascade delete clinical parameters
      Object.keys(db.clinical_parameters).forEach(paramId => {
        if (db.clinical_parameters[paramId].record_id === recordId) {
          delete db.clinical_parameters[paramId];
        }
      });
      
      await saveDB(db);
    }
  }
};

export const ClinicalParameterRepository = {
  async save(param: ClinicalParameter): Promise<void> {
    const db = await loadDB();
    const dict = param.toDict();
    db.clinical_parameters[param.param_id] = dict;
    await saveDB(db);
  },

  async saveMany(params: ClinicalParameter[]): Promise<void> {
    const db = await loadDB();
    params.forEach(param => {
      db.clinical_parameters[param.param_id] = param.toDict();
    });
    await saveDB(db);
  },

  async findByRecordId(recordId: string): Promise<ClinicalParameter[]> {
    const db = await loadDB();
    return Object.values(db.clinical_parameters)
      .filter(cp => cp.record_id === recordId)
      .map(cp => ClinicalParameter.fromDict(cp));
  },

  async findByParamName(paramName: string, userId: string = 'local_user'): Promise<ClinicalParameter[]> {
    const db = await loadDB();
    const params = Object.values(db.clinical_parameters)
      .filter(cp => {
        const record = db.health_records[cp.record_id];
        return cp.param_name === paramName && record && record.user_id === userId && record.is_deleted === 0;
      })
      .map(cp => ClinicalParameter.fromDict(cp));

    // Sort report_date ascending for trend timeline charts
    return params.sort((a, b) => a.report_date.getTime() - b.report_date.getTime());
  },

  async findAll(userId: string = 'local_user'): Promise<ClinicalParameter[]> {
    const db = await loadDB();
    const params = Object.values(db.clinical_parameters)
      .filter(cp => {
        const record = db.health_records[cp.record_id];
        return record && record.user_id === userId && record.is_deleted === 0;
      })
      .map(cp => ClinicalParameter.fromDict(cp));

    return params.sort((a, b) => b.report_date.getTime() - a.report_date.getTime());
  },

  async update(paramId: string, value: number, status: string): Promise<void> {
    const db = await loadDB();
    if (db.clinical_parameters[paramId]) {
      db.clinical_parameters[paramId].value = value;
      db.clinical_parameters[paramId].status = status;
      await saveDB(db);
    }
  }
};

export const RiskScoreRepository = {
  async save(score: RiskScore): Promise<void> {
    const db = await loadDB();
    const dict = score.toDict();
    db.risk_scores[score.score_id] = dict;
    await saveDB(db);
  },

  async findLatest(userId: string = 'local_user'): Promise<RiskScore | null> {
    const db = await loadDB();
    const scores = Object.values(db.risk_scores)
      .filter(s => s.user_id === userId)
      .map(s => RiskScore.fromDict(s));

    if (scores.length === 0) return null;
    
    // Sort computed_at descending and get first
    scores.sort((a, b) => b.computed_at.getTime() - a.computed_at.getTime());
    return scores[0];
  },

  async getHistory(userId: string = 'local_user'): Promise<RiskScore[]> {
    const db = await loadDB();
    const scores = Object.values(db.risk_scores)
      .filter(s => s.user_id === userId)
      .map(s => RiskScore.fromDict(s));

    // Sort computed_at ascending
    return scores.sort((a, b) => a.computed_at.getTime() - b.computed_at.getTime());
  }
};

export const ReminderRepository = {
  async save(reminder: Reminder): Promise<void> {
    const db = await loadDB();
    const dict = reminder.toDict();
    db.reminders[reminder.reminder_id] = dict;
    await saveDB(db);
  },

  async findById(reminderId: string): Promise<Reminder | null> {
    const db = await loadDB();
    const row = db.reminders[reminderId];
    if (!row) return null;
    return Reminder.fromDict(row);
  },

  async findActive(userId: string = 'local_user'): Promise<Reminder[]> {
    const db = await loadDB();
    const reminders = Object.values(db.reminders)
      .filter(r => r.user_id === userId && r.is_active === 1)
      .map(r => Reminder.fromDict(r));

    return reminders.sort((a, b) => a.due_date.getTime() - b.due_date.getTime());
  },

  async findAll(userId: string = 'local_user'): Promise<Reminder[]> {
    const db = await loadDB();
    const reminders = Object.values(db.reminders)
      .filter(r => r.user_id === userId)
      .map(r => Reminder.fromDict(r));

    return reminders.sort((a, b) => a.due_date.getTime() - b.due_date.getTime());
  },

  async delete(reminderId: string): Promise<void> {
    const db = await loadDB();
    if (db.reminders[reminderId]) {
      delete db.reminders[reminderId];
      await saveDB(db);
    }
  },

  async acknowledge(reminderId: string, isAck: boolean = true): Promise<void> {
    const db = await loadDB();
    if (db.reminders[reminderId]) {
      db.reminders[reminderId].is_acknowledged = isAck ? 1 : 0;
      await saveDB(db);
    }
  }
};

export const DoctorReportRepository = {
  async save(report: DoctorReport): Promise<void> {
    const db = await loadDB();
    const dict = report.toDict();
    db.doctor_reports[report.report_id] = dict;
    await saveDB(db);
  },

  async findLatest(userId: string = 'local_user'): Promise<DoctorReport | null> {
    const db = await loadDB();
    const reports = Object.values(db.doctor_reports)
      .filter(r => r.user_id === userId)
      .map(r => DoctorReport.fromDict(r));

    if (reports.length === 0) return null;

    reports.sort((a, b) => b.generated_at.getTime() - a.generated_at.getTime());
    return reports[0];
  },

  async findById(reportId: string): Promise<DoctorReport | null> {
    const db = await loadDB();
    const row = db.doctor_reports[reportId];
    if (!row) return null;
    return DoctorReport.fromDict(row);
  },

  async findByShareToken(token: string): Promise<DoctorReport | null> {
    const db = await loadDB();
    const row = Object.values(db.doctor_reports).find(r => r.share_token === token);
    if (!row) return null;
    return DoctorReport.fromDict(row);
  }
};
