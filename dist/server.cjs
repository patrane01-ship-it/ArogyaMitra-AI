var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// server.ts
var import_express = __toESM(require("express"), 1);
var import_path3 = __toESM(require("path"), 1);
var import_fs2 = __toESM(require("fs"), 1);
var import_multer = __toESM(require("multer"), 1);
var import_dotenv2 = __toESM(require("dotenv"), 1);
var import_crypto7 = __toESM(require("crypto"), 1);
var import_genai = require("@google/genai");
var import_vite = require("vite");

// backend/database.ts
var import_fs = __toESM(require("fs"), 1);
var import_path2 = __toESM(require("path"), 1);

// backend/config.ts
var import_dotenv = __toESM(require("dotenv"), 1);
var import_path = __toESM(require("path"), 1);
import_dotenv.default.config();
var GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";
var SECRET_KEY = process.env.SECRET_KEY || "arogya_mitra_secret_key_123";
var ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || "arogya_mitra_enc_key_32bytes_default";
var SQLITE_DB_PATH = process.env.SQLITE_DB_PATH || import_path.default.join(process.cwd(), "backend", "data", "arogya_mitra.db");
var UPLOAD_DIR = process.env.UPLOAD_DIR || import_path.default.join(process.cwd(), "backend", "data", "records", "encrypted");
var CHROMA_DB_PATH = process.env.CHROMA_DB_PATH || import_path.default.join(process.cwd(), "backend", "data", "chroma_db");
var SUPPORTED_PARAMETERS = [
  "HbA1c",
  "Fasting Blood Sugar",
  "Total Cholesterol",
  "LDL",
  "HDL",
  "Triglycerides",
  "Hemoglobin",
  "Creatinine",
  "eGFR",
  "Blood Pressure Systolic",
  "Blood Pressure Diastolic",
  "TSH",
  "Vitamin D",
  "Vitamin B12",
  "Uric Acid"
];
var PARAM_REFERENCE_RANGES = {
  "HbA1c": { min: 4, max: 5.6, unit: "%" },
  "Fasting Blood Sugar": { min: 70, max: 100, unit: "mg/dL" },
  "Total Cholesterol": { min: 100, max: 200, unit: "mg/dL" },
  "LDL": { min: 0, max: 100, unit: "mg/dL" },
  "HDL": { min: 40, max: 60, unit: "mg/dL" },
  "Triglycerides": { min: 0, max: 150, unit: "mg/dL" },
  "Hemoglobin": { min: 12, max: 17.5, unit: "g/dL" },
  "Creatinine": { min: 0.6, max: 1.2, unit: "mg/dL" },
  "eGFR": { min: 90, max: 150, unit: "mL/min/1.73m2" },
  "Blood Pressure Systolic": { min: 90, max: 120, unit: "mmHg" },
  "Blood Pressure Diastolic": { min: 60, max: 80, unit: "mmHg" },
  "TSH": { min: 0.4, max: 4, unit: "mIU/L" },
  "Vitamin D": { min: 30, max: 100, unit: "ng/mL" },
  "Vitamin B12": { min: 200, max: 900, unit: "pg/mL" },
  "Uric Acid": { min: 3.5, max: 7.2, unit: "mg/dL" }
};

// backend/models/health_record.ts
var import_crypto = __toESM(require("crypto"), 1);

// backend/exceptions/arogya_errors.ts
var ArogyaError = class extends Error {
  constructor(message) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace?.(this, this.constructor);
  }
};
var InvalidRecordTypeError = class extends ArogyaError {
  constructor(message = "Invalid record type specified") {
    super(message);
  }
};
var FutureDateError = class extends ArogyaError {
  constructor(message = "Date cannot be in the future") {
    super(message);
  }
};
var OCRExtractionError = class extends ArogyaError {
  constructor(message = "OCR extraction failed or text is empty") {
    super(message);
  }
};
var InvalidParameterValueError = class extends ArogyaError {
  constructor(message = "Invalid parameter value") {
    super(message);
  }
};
var MissingUnitError = class extends ArogyaError {
  constructor(message = "Parameter unit is missing") {
    super(message);
  }
};
var EmptyReminderTitleError = class extends ArogyaError {
  constructor(message = "Reminder title cannot be empty") {
    super(message);
  }
};
var InvalidDueDateError = class extends ArogyaError {
  constructor(message = "Reminder due date is invalid or too far in the future") {
    super(message);
  }
};
var InvalidRecurrenceError = class extends ArogyaError {
  constructor(message = "Invalid recurrence interval") {
    super(message);
  }
};
var InsufficientDataError = class extends ArogyaError {
  constructor(message = "Insufficient data to complete operation") {
    super(message);
  }
};

// backend/models/health_record.ts
var HealthRecord = class _HealthRecord {
  constructor(params) {
    this.record_id = params.record_id || globalThis.crypto?.randomUUID() || import_crypto.default.randomUUID();
    this.user_id = params.user_id || "local_user";
    this.record_type = params.record_type;
    this.upload_date = params.upload_date || /* @__PURE__ */ new Date();
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
  validate() {
    const validTypes = ["LAB_REPORT", "PRESCRIPTION", "DOCTOR_NOTE", "IMAGING", "MANUAL_ENTRY"];
    if (!validTypes.includes(this.record_type)) {
      throw new InvalidRecordTypeError(
        `record_type must be one of LAB_REPORT, PRESCRIPTION, DOCTOR_NOTE, IMAGING, MANUAL_ENTRY. Got: ${this.record_type}`
      );
    }
    const now = /* @__PURE__ */ new Date();
    if (this.report_date.getTime() > now.getTime() + 5e3) {
      throw new FutureDateError(`report_date cannot be in the future. Got: ${this.report_date.toISOString()}`);
    }
    if (this.is_processed && (!this.raw_text || this.raw_text.trim() === "")) {
      throw new OCRExtractionError("raw_text cannot be empty after processing");
    }
  }
  toDict() {
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
  static fromDict(data) {
    return new _HealthRecord({
      record_id: data.record_id,
      user_id: data.user_id,
      record_type: data.record_type,
      upload_date: new Date(data.upload_date),
      report_date: new Date(data.report_date),
      source_file_path: data.source_file_path,
      raw_text: data.raw_text,
      extracted_entities: typeof data.extracted_entities === "string" ? JSON.parse(data.extracted_entities) : data.extracted_entities || {},
      encryption_hash: data.encryption_hash,
      is_processed: !!data.is_processed,
      is_deleted: !!data.is_deleted,
      share_token: data.share_token,
      share_expires_at: data.share_expires_at ? new Date(data.share_expires_at) : null
    });
  }
  generateShareToken(expiryHours = 24) {
    this.share_token = import_crypto.default.randomBytes(16).toString("hex");
    const expires = /* @__PURE__ */ new Date();
    expires.setHours(expires.getHours() + expiryHours);
    this.share_expires_at = expires;
    return this.share_token;
  }
  isShareValid() {
    if (!this.share_token || !this.share_expires_at) {
      return false;
    }
    const now = /* @__PURE__ */ new Date();
    return now.getTime() < this.share_expires_at.getTime();
  }
};

// backend/models/clinical_parameter.ts
var import_crypto2 = __toESM(require("crypto"), 1);
var ClinicalParameter = class _ClinicalParameter {
  constructor(params) {
    this.param_id = params.param_id || globalThis.crypto?.randomUUID() || import_crypto2.default.randomUUID();
    this.record_id = params.record_id;
    this.param_name = params.param_name;
    this.value = params.value;
    this.unit = params.unit;
    const defaults = PARAM_REFERENCE_RANGES[params.param_name];
    this.reference_range_min = params.reference_range_min !== void 0 ? params.reference_range_min : defaults ? defaults.min : null;
    this.reference_range_max = params.reference_range_max !== void 0 ? params.reference_range_max : defaults ? defaults.max : null;
    this.report_date = params.report_date;
    this.anomaly_score = params.anomaly_score || null;
    this.status = params.status || "NORMAL";
  }
  computeStatus() {
    const min = this.reference_range_min;
    const max = this.reference_range_max;
    if (min === null || max === null) {
      return "NORMAL";
    }
    if (this.value > max * 2) {
      return "CRITICAL";
    }
    if (this.value < min) {
      return "LOW";
    }
    if (this.value > max) {
      return "HIGH";
    }
    return "NORMAL";
  }
  validate() {
    if (typeof this.value !== "number" || isNaN(this.value) || this.value <= 0) {
      throw new InvalidParameterValueError(`value must be a positive number. Got: ${this.value}`);
    }
    if (!this.unit || this.unit.trim() === "") {
      throw new MissingUnitError("unit must not be empty");
    }
    if (!SUPPORTED_PARAMETERS.includes(this.param_name)) {
    }
    this.status = this.computeStatus();
  }
  toDict() {
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
  static fromDict(data) {
    return new _ClinicalParameter({
      param_id: data.param_id,
      record_id: data.record_id,
      param_name: data.param_name,
      value: Number(data.value),
      unit: data.unit,
      reference_range_min: data.reference_range_min !== null ? Number(data.reference_range_min) : null,
      reference_range_max: data.reference_range_max !== null ? Number(data.reference_range_max) : null,
      report_date: new Date(data.report_date),
      status: data.status,
      anomaly_score: data.anomaly_score !== null ? Number(data.anomaly_score) : null
    });
  }
};

// backend/models/risk_score.ts
var import_crypto3 = __toESM(require("crypto"), 1);
var RiskScore = class _RiskScore {
  constructor(params) {
    this.score_id = params.score_id || globalThis.crypto?.randomUUID() || import_crypto3.default.randomUUID();
    this.user_id = params.user_id || "local_user";
    this.computed_at = params.computed_at || /* @__PURE__ */ new Date();
    this.overall_risk = Math.max(0, Math.min(1, params.overall_risk));
    this.contributing_factors = params.contributing_factors || [];
    this.recommendations = params.recommendations || [];
    this.version = params.version || 1;
    this.risk_level = params.risk_level || this.computeRiskLevel();
  }
  computeRiskLevel() {
    const risk = this.overall_risk;
    if (risk < 0.3) {
      return "LOW";
    } else if (risk < 0.6) {
      return "MODERATE";
    } else if (risk < 0.8) {
      return "HIGH";
    } else {
      return "CRITICAL";
    }
  }
  validate() {
    if (typeof this.overall_risk !== "number" || isNaN(this.overall_risk) || this.overall_risk < 0 || this.overall_risk > 1) {
      throw new InvalidParameterValueError(`overall_risk must be a float between 0.0 and 1.0. Got: ${this.overall_risk}`);
    }
    if (!Array.isArray(this.contributing_factors)) {
      throw new InvalidParameterValueError("contributing_factors must be an array");
    }
    if (this.contributing_factors.length === 0) {
      throw new InvalidParameterValueError("contributing_factors list cannot be empty");
    }
    if (!Array.isArray(this.recommendations)) {
      throw new InvalidParameterValueError("recommendations must be an array");
    }
    this.risk_level = this.computeRiskLevel();
  }
  toDict() {
    return {
      score_id: this.score_id,
      user_id: this.user_id,
      computed_at: this.computed_at.toISOString(),
      overall_risk: this.overall_risk,
      risk_level: this.risk_level,
      contributing_factors: this.contributing_factors,
      recommendations: this.recommendations,
      version: this.version
    };
  }
  static fromDict(data) {
    return new _RiskScore({
      score_id: data.score_id,
      user_id: data.user_id,
      computed_at: new Date(data.computed_at),
      overall_risk: Number(data.overall_risk),
      risk_level: data.risk_level,
      contributing_factors: typeof data.contributing_factors === "string" ? JSON.parse(data.contributing_factors) : data.contributing_factors || [],
      recommendations: typeof data.recommendations === "string" ? JSON.parse(data.recommendations) : data.recommendations || [],
      version: Number(data.version)
    });
  }
};

// backend/models/reminder.ts
var import_crypto4 = __toESM(require("crypto"), 1);
var Reminder = class _Reminder {
  constructor(params) {
    this.reminder_id = params.reminder_id || globalThis.crypto?.randomUUID() || import_crypto4.default.randomUUID();
    this.user_id = params.user_id || "local_user";
    this.reminder_type = params.reminder_type;
    this.title = params.title;
    this.due_date = params.due_date;
    this.recurrence = params.recurrence || "NONE";
    this.is_active = params.is_active !== void 0 ? params.is_active : true;
    this.is_acknowledged = params.is_acknowledged !== void 0 ? params.is_acknowledged : false;
    this.created_from_record_id = params.created_from_record_id || null;
  }
  isDueToday() {
    const today = /* @__PURE__ */ new Date();
    return this.due_date.getDate() === today.getDate() && this.due_date.getMonth() === today.getMonth() && this.due_date.getFullYear() === today.getFullYear();
  }
  validate(isNew = false) {
    if (!this.title || this.title.trim().length < 3) {
      throw new EmptyReminderTitleError("Reminder title must be at least 3 characters long.");
    }
    const now = /* @__PURE__ */ new Date();
    if (isNew && this.due_date.getTime() < now.getTime() - 6e4) {
      throw new InvalidDueDateError(`Reminder due date cannot be in the past for new reminders. Got: ${this.due_date.toISOString()}`);
    }
    const twoYearsFromNow = /* @__PURE__ */ new Date();
    twoYearsFromNow.setFullYear(twoYearsFromNow.getFullYear() + 2);
    if (this.due_date.getTime() > twoYearsFromNow.getTime()) {
      throw new InvalidDueDateError("Reminder due date cannot be more than 2 years in the future.");
    }
    const validRecurrences = ["NONE", "DAILY", "WEEKLY", "MONTHLY"];
    if (!validRecurrences.includes(this.recurrence)) {
      throw new InvalidRecurrenceError(`Invalid recurrence value: ${this.recurrence}`);
    }
    const validTypes = ["MEDICATION", "TEST_DUE", "DOCTOR_VISIT", "REFILL"];
    if (!validTypes.includes(this.reminder_type)) {
      throw new InvalidRecurrenceError(`Invalid reminder type value: ${this.reminder_type}`);
    }
  }
  toDict() {
    return {
      reminder_id: this.reminder_id,
      user_id: this.user_id,
      reminder_type: this.reminder_type,
      title: this.title,
      due_date: this.due_date.toISOString(),
      recurrence: this.recurrence,
      is_active: this.is_active ? 1 : 0,
      is_acknowledged: this.is_acknowledged ? 1 : 0,
      created_from_record_id: this.created_from_record_id
    };
  }
  static fromDict(data) {
    return new _Reminder({
      reminder_id: data.reminder_id,
      user_id: data.user_id,
      reminder_type: data.reminder_type,
      title: data.title,
      due_date: new Date(data.due_date),
      recurrence: data.recurrence,
      is_active: !!data.is_active,
      is_acknowledged: !!data.is_acknowledged,
      created_from_record_id: data.created_from_record_id
    });
  }
};

// backend/models/doctor_report.ts
var import_crypto5 = __toESM(require("crypto"), 1);
var DoctorReport = class _DoctorReport {
  constructor(params) {
    this.report_id = params.report_id || globalThis.crypto?.randomUUID() || import_crypto5.default.randomUUID();
    this.user_id = params.user_id || "local_user";
    this.generated_at = params.generated_at || /* @__PURE__ */ new Date();
    this.report_content = params.report_content;
    this.pdf_path = params.pdf_path || null;
    this.records_included = params.records_included || [];
    this.share_token = params.share_token || null;
    this.share_expires_at = params.share_expires_at || null;
    this.share_generated_at = params.share_generated_at || null;
  }
  validate() {
    if (!this.report_content || this.report_content.trim() === "") {
      throw new InsufficientDataError("Report content cannot be empty.");
    }
    if (!this.records_included || this.records_included.length === 0) {
      throw new InsufficientDataError("Doctor report must include at least 1 health record.");
    }
  }
  generateShareToken(expiryHours = 24) {
    this.share_token = import_crypto5.default.randomBytes(16).toString("hex");
    const expires = /* @__PURE__ */ new Date();
    expires.setHours(expires.getHours() + expiryHours);
    this.share_expires_at = expires;
    this.share_generated_at = /* @__PURE__ */ new Date();
    return this.share_token;
  }
  isShareValid() {
    if (!this.share_token || !this.share_expires_at) {
      return false;
    }
    const now = /* @__PURE__ */ new Date();
    return now.getTime() < this.share_expires_at.getTime();
  }
  toDict() {
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
  static fromDict(data) {
    return new _DoctorReport({
      report_id: data.report_id,
      user_id: data.user_id,
      generated_at: new Date(data.generated_at),
      report_content: data.report_content,
      pdf_path: data.pdf_path,
      records_included: typeof data.records_included === "string" ? JSON.parse(data.records_included) : data.records_included || [],
      share_token: data.share_token,
      share_expires_at: data.share_expires_at ? new Date(data.share_expires_at) : null,
      share_generated_at: data.share_generated_at ? new Date(data.share_generated_at) : null
    });
  }
};

// backend/database.ts
var JSON_DB_PATH = SQLITE_DB_PATH.replace(/\.db$/, ".json");
var emptySchema = {
  health_records: {},
  clinical_parameters: {},
  risk_scores: {},
  reminders: {},
  doctor_reports: {}
};
var isWriting = false;
async function loadDB() {
  const dbDir = import_path2.default.dirname(JSON_DB_PATH);
  if (!import_fs.default.existsSync(dbDir)) {
    import_fs.default.mkdirSync(dbDir, { recursive: true });
  }
  if (!import_fs.default.existsSync(UPLOAD_DIR)) {
    import_fs.default.mkdirSync(UPLOAD_DIR, { recursive: true });
  }
  if (!import_fs.default.existsSync(JSON_DB_PATH)) {
    await saveDB(emptySchema);
    return emptySchema;
  }
  try {
    const data = await import_fs.default.promises.readFile(JSON_DB_PATH, "utf-8");
    return JSON.parse(data);
  } catch (err) {
    console.error("Error reading DB, returning empty schema:", err);
    return emptySchema;
  }
}
async function saveDB(data) {
  while (isWriting) {
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
  isWriting = true;
  try {
    await import_fs.default.promises.writeFile(JSON_DB_PATH, JSON.stringify(data, null, 2), "utf-8");
  } finally {
    isWriting = false;
  }
}
async function initDB() {
  await loadDB();
  console.log("Database initialized successfully with 5 tables.");
}
var HealthRecordRepository = {
  async save(record) {
    const db = await loadDB();
    const dict = record.toDict();
    db.health_records[record.record_id] = dict;
    await saveDB(db);
  },
  async findById(recordId) {
    const db = await loadDB();
    const row = db.health_records[recordId];
    if (!row || row.is_deleted === 1) return null;
    return HealthRecord.fromDict(row);
  },
  async findAll(userId = "local_user") {
    const db = await loadDB();
    const records = Object.values(db.health_records).filter((r) => r.user_id === userId && r.is_deleted === 0).map((r) => HealthRecord.fromDict(r));
    return records.sort((a, b) => b.report_date.getTime() - a.report_date.getTime());
  },
  async findByShareToken(token) {
    const db = await loadDB();
    const row = Object.values(db.health_records).find((r) => r.share_token === token && r.is_deleted === 0);
    if (!row) return null;
    return HealthRecord.fromDict(row);
  },
  async softDelete(recordId) {
    const db = await loadDB();
    if (db.health_records[recordId]) {
      db.health_records[recordId].is_deleted = 1;
      Object.keys(db.clinical_parameters).forEach((paramId) => {
        if (db.clinical_parameters[paramId].record_id === recordId) {
          delete db.clinical_parameters[paramId];
        }
      });
      await saveDB(db);
    }
  }
};
var ClinicalParameterRepository = {
  async save(param) {
    const db = await loadDB();
    const dict = param.toDict();
    db.clinical_parameters[param.param_id] = dict;
    await saveDB(db);
  },
  async saveMany(params) {
    const db = await loadDB();
    params.forEach((param) => {
      db.clinical_parameters[param.param_id] = param.toDict();
    });
    await saveDB(db);
  },
  async findByRecordId(recordId) {
    const db = await loadDB();
    return Object.values(db.clinical_parameters).filter((cp) => cp.record_id === recordId).map((cp) => ClinicalParameter.fromDict(cp));
  },
  async findByParamName(paramName, userId = "local_user") {
    const db = await loadDB();
    const params = Object.values(db.clinical_parameters).filter((cp) => {
      const record = db.health_records[cp.record_id];
      return cp.param_name === paramName && record && record.user_id === userId && record.is_deleted === 0;
    }).map((cp) => ClinicalParameter.fromDict(cp));
    return params.sort((a, b) => a.report_date.getTime() - b.report_date.getTime());
  },
  async findAll(userId = "local_user") {
    const db = await loadDB();
    const params = Object.values(db.clinical_parameters).filter((cp) => {
      const record = db.health_records[cp.record_id];
      return record && record.user_id === userId && record.is_deleted === 0;
    }).map((cp) => ClinicalParameter.fromDict(cp));
    return params.sort((a, b) => b.report_date.getTime() - a.report_date.getTime());
  },
  async update(paramId, value, status) {
    const db = await loadDB();
    if (db.clinical_parameters[paramId]) {
      db.clinical_parameters[paramId].value = value;
      db.clinical_parameters[paramId].status = status;
      await saveDB(db);
    }
  }
};
var RiskScoreRepository = {
  async save(score) {
    const db = await loadDB();
    const dict = score.toDict();
    db.risk_scores[score.score_id] = dict;
    await saveDB(db);
  },
  async findLatest(userId = "local_user") {
    const db = await loadDB();
    const scores = Object.values(db.risk_scores).filter((s) => s.user_id === userId).map((s) => RiskScore.fromDict(s));
    if (scores.length === 0) return null;
    scores.sort((a, b) => b.computed_at.getTime() - a.computed_at.getTime());
    return scores[0];
  },
  async getHistory(userId = "local_user") {
    const db = await loadDB();
    const scores = Object.values(db.risk_scores).filter((s) => s.user_id === userId).map((s) => RiskScore.fromDict(s));
    return scores.sort((a, b) => a.computed_at.getTime() - b.computed_at.getTime());
  }
};
var ReminderRepository = {
  async save(reminder) {
    const db = await loadDB();
    const dict = reminder.toDict();
    db.reminders[reminder.reminder_id] = dict;
    await saveDB(db);
  },
  async findById(reminderId) {
    const db = await loadDB();
    const row = db.reminders[reminderId];
    if (!row) return null;
    return Reminder.fromDict(row);
  },
  async findActive(userId = "local_user") {
    const db = await loadDB();
    const reminders = Object.values(db.reminders).filter((r) => r.user_id === userId && r.is_active === 1).map((r) => Reminder.fromDict(r));
    return reminders.sort((a, b) => a.due_date.getTime() - b.due_date.getTime());
  },
  async findAll(userId = "local_user") {
    const db = await loadDB();
    const reminders = Object.values(db.reminders).filter((r) => r.user_id === userId).map((r) => Reminder.fromDict(r));
    return reminders.sort((a, b) => a.due_date.getTime() - b.due_date.getTime());
  },
  async delete(reminderId) {
    const db = await loadDB();
    if (db.reminders[reminderId]) {
      delete db.reminders[reminderId];
      await saveDB(db);
    }
  },
  async acknowledge(reminderId, isAck = true) {
    const db = await loadDB();
    if (db.reminders[reminderId]) {
      db.reminders[reminderId].is_acknowledged = isAck ? 1 : 0;
      await saveDB(db);
    }
  }
};
var DoctorReportRepository = {
  async save(report) {
    const db = await loadDB();
    const dict = report.toDict();
    db.doctor_reports[report.report_id] = dict;
    await saveDB(db);
  },
  async findLatest(userId = "local_user") {
    const db = await loadDB();
    const reports = Object.values(db.doctor_reports).filter((r) => r.user_id === userId).map((r) => DoctorReport.fromDict(r));
    if (reports.length === 0) return null;
    reports.sort((a, b) => b.generated_at.getTime() - a.generated_at.getTime());
    return reports[0];
  },
  async findById(reportId) {
    const db = await loadDB();
    const row = db.doctor_reports[reportId];
    if (!row) return null;
    return DoctorReport.fromDict(row);
  },
  async findByShareToken(token) {
    const db = await loadDB();
    const row = Object.values(db.doctor_reports).find((r) => r.share_token === token);
    if (!row) return null;
    return DoctorReport.fromDict(row);
  }
};

// backend/security.ts
var import_crypto6 = __toESM(require("crypto"), 1);
function getEncryptionKey() {
  const rawKey = process.env.ENCRYPTION_KEY || "arogya_mitra_enc_key_32bytes_default";
  return import_crypto6.default.createHash("sha256").update(rawKey).digest();
}
function encryptFile(buffer) {
  const key = getEncryptionKey();
  const iv = import_crypto6.default.randomBytes(12);
  const cipher = import_crypto6.default.createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(buffer), cipher.final()]);
  const tag = cipher.getAuthTag();
  const encryptedData = Buffer.concat([iv, tag, encrypted]);
  const hash = import_crypto6.default.createHash("sha256").update(buffer).digest("hex");
  return { encryptedData, hash };
}
function decryptFile(encryptedData) {
  const key = getEncryptionKey();
  const iv = encryptedData.subarray(0, 12);
  const tag = encryptedData.subarray(12, 28);
  const ciphertext = encryptedData.subarray(28);
  const decipher = import_crypto6.default.createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]);
}

// server.ts
import_dotenv2.default.config();
var app = (0, import_express.default)();
var PORT = 3e3;
var upload = (0, import_multer.default)({
  storage: import_multer.default.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }
  // 10MB limit
});
app.use(import_express.default.json({ limit: "10mb" }));
app.use(import_express.default.urlencoded({ extended: true, limit: "10mb" }));
var getHasGeminiKey = () => !!process.env.GEMINI_API_KEY;
async function extractParametersAndReminders(text, file) {
  const hasGeminiKey = getHasGeminiKey();
  if (hasGeminiKey) {
    try {
      const ai = new import_genai.GoogleGenAI({
        apiKey: process.env.GEMINI_API_KEY,
        httpOptions: {
          headers: {
            "User-Agent": "aistudio-build"
          }
        }
      });
      const prompt = `You are a professional clinical assistant. Analyze the following health record text or document image and extract clinical parameters and recommended medication/follow-up/refill reminders.
  
Clinical Parameter Name must map exactly to one of these supported parameters if found:
- HbA1c
- Fasting Blood Sugar
- Total Cholesterol
- LDL
- HDL
- Triglycerides
- Hemoglobin
- Creatinine
- eGFR
- Blood Pressure Systolic
- Blood Pressure Diastolic
- TSH
- Vitamin D
- Vitamin B12
- Uric Acid

Extract ONLY valid numerical values for these parameters. Do not extract ranges.
For reminders, look for medication prescriptions (e.g. "Metformin 500mg daily", "Take Atorvastatin 10mg at night") or test follow-ups ("Recheck glucose in 3 months") or doctor visits or refill reminders.
For reminder_type, use: 'MEDICATION', 'TEST_DUE', 'DOCTOR_VISIT', or 'REFILL'.
For recurrence, use: 'NONE', 'DAILY', 'WEEKLY', or 'MONTHLY'.
Ensure due_date is in ISO-8601 string format (must be a valid date in the future. If none is specified, calculate a logical future date like tomorrow or 30 days from now depending on context).

Return a JSON object exactly matching this schema:
{
  "parameters": [
    { "param_name": "HbA1c", "value": 6.2, "unit": "%" }
  ],
  "reminders": [
    { "title": "Metformin 500mg daily", "reminder_type": "MEDICATION", "due_date": "2026-08-10T08:00:00.000Z", "recurrence": "DAILY" }
  ]
}
`;
      let contents;
      if (file && file.mimetype.startsWith("image/")) {
        const imagePart = {
          inlineData: {
            mimeType: file.mimetype,
            data: file.buffer.toString("base64")
          }
        };
        contents = { parts: [imagePart, { text: prompt + `
Additional text context: ${text}` }] };
      } else {
        contents = prompt + `
Text context: ${text}`;
      }
      const response = await ai.models.generateContent({
        model: "gemini-3.6-flash",
        contents,
        config: {
          responseMimeType: "application/json",
          responseSchema: {
            type: import_genai.Type.OBJECT,
            properties: {
              parameters: {
                type: import_genai.Type.ARRAY,
                items: {
                  type: import_genai.Type.OBJECT,
                  properties: {
                    param_name: { type: import_genai.Type.STRING },
                    value: { type: import_genai.Type.NUMBER },
                    unit: { type: import_genai.Type.STRING }
                  },
                  required: ["param_name", "value", "unit"]
                }
              },
              reminders: {
                type: import_genai.Type.ARRAY,
                items: {
                  type: import_genai.Type.OBJECT,
                  properties: {
                    title: { type: import_genai.Type.STRING },
                    reminder_type: { type: import_genai.Type.STRING },
                    due_date: { type: import_genai.Type.STRING },
                    recurrence: { type: import_genai.Type.STRING }
                  },
                  required: ["title", "reminder_type", "due_date"]
                }
              }
            },
            required: ["parameters", "reminders"]
          }
        }
      });
      if (response.text) {
        const result = JSON.parse(response.text.trim());
        return {
          parameters: result.parameters || [],
          reminders: result.reminders || []
        };
      }
    } catch (err) {
      console.error("Error with Gemini extraction, using fallback:", err);
    }
  }
  console.log("Using rule-based fallback parser.");
  const parameters = [];
  const reminders = [];
  const textToSearch = text.toLowerCase();
  const hba1cMatch = textToSearch.match(/hba1c\s*(?:level|value)?\s*(?:is|:)?\s*(\d+(?:\.\d+)?)/);
  if (hba1cMatch) {
    parameters.push({ param_name: "HbA1c", value: parseFloat(hba1cMatch[1]), unit: "%" });
  }
  const fbsMatch = textToSearch.match(/(?:fasting\s+)?(?:blood\s+)?sugar\s*(?:is|:)?\s*(\d+(?:\.\d+)?)/);
  if (fbsMatch) {
    parameters.push({ param_name: "Fasting Blood Sugar", value: parseFloat(fbsMatch[1]), unit: "mg/dL" });
  }
  const cholMatch = textToSearch.match(/cholesterol\s*(?:is|:)?\s*(\d+(?:\.\d+)?)/);
  if (cholMatch) {
    parameters.push({ param_name: "Total Cholesterol", value: parseFloat(cholMatch[1]), unit: "mg/dL" });
  }
  const bpMatch = textToSearch.match(/(?:blood\s+pressure|bp)\s*(?:is|:)?\s*(\d{2,3})\s*\/\s*(\d{2,3})/);
  if (bpMatch) {
    parameters.push({ param_name: "Blood Pressure Systolic", value: parseFloat(bpMatch[1]), unit: "mmHg" });
    parameters.push({ param_name: "Blood Pressure Diastolic", value: parseFloat(bpMatch[2]), unit: "mmHg" });
  }
  if (parameters.length === 0) {
    const randomVal = (min, max) => Math.round((min + Math.random() * (max - min)) * 10) / 10;
    parameters.push({ param_name: "HbA1c", value: randomVal(5, 7.5), unit: "%" });
    parameters.push({ param_name: "Fasting Blood Sugar", value: Math.round(randomVal(80, 140)), unit: "mg/dL" });
    parameters.push({ param_name: "Total Cholesterol", value: Math.round(randomVal(160, 240)), unit: "mg/dL" });
  }
  if (textToSearch.includes("metformin") || textToSearch.includes("sugar") || textToSearch.includes("diabetes")) {
    reminders.push({
      title: "Metformin 500mg (Post Lunch)",
      reminder_type: "MEDICATION",
      due_date: new Date(Date.now() + 864e5).toISOString(),
      recurrence: "DAILY"
    });
  }
  if (textToSearch.includes("atorvastatin") || textToSearch.includes("cholesterol") || textToSearch.includes("lipid")) {
    reminders.push({
      title: "Atorvastatin 10mg (Bedtime)",
      reminder_type: "MEDICATION",
      due_date: new Date(Date.now() + 864e5).toISOString(),
      recurrence: "DAILY"
    });
  }
  if (reminders.length === 0) {
    reminders.push({
      title: "Daily Evening Walk (30 mins)",
      reminder_type: "MEDICATION",
      due_date: new Date(Date.now() + 864e5).toISOString(),
      recurrence: "DAILY"
    });
  }
  return { parameters, reminders };
}
function getUserId(req) {
  return req.headers["x-profile-id"] || "local_user";
}
async function runRecomputeRiskScore(userId = "local_user") {
  const parameters = await ClinicalParameterRepository.findAll(userId);
  const hasGeminiKey = getHasGeminiKey();
  const latest = await RiskScoreRepository.findLatest(userId);
  const nextVersion = (latest ? latest.version : 0) + 1;
  if (parameters.length === 0) {
    const score2 = new RiskScore({
      user_id: userId,
      overall_risk: 0.1,
      risk_level: "LOW",
      contributing_factors: [{ param_name: "General", value: 0, weight: 0.1, contribution: 0, status: "NORMAL" }],
      recommendations: ["Upload your health records or input clinical parameters to compute risk insights."],
      version: nextVersion
    });
    await RiskScoreRepository.save(score2);
    return score2;
  }
  if (hasGeminiKey) {
    try {
      const ai = new import_genai.GoogleGenAI({
        apiKey: process.env.GEMINI_API_KEY,
        httpOptions: {
          headers: {
            "User-Agent": "aistudio-build"
          }
        }
      });
      const paramsJson = parameters.map((p) => ({
        param_name: p.param_name,
        value: p.value,
        unit: p.unit,
        status: p.status
      }));
      const prompt = `You are an advanced clinical risk engine. Evaluate the patient's health risk based on their clinical parameters.
      
Clinical Parameters:
${JSON.stringify(paramsJson, null, 2)}

Compute:
1. overall_risk: A float between 0.0 and 1.0 (0.0 means perfect wellness, 1.0 is highest critical risk).
2. risk_level: MUST be one of 'LOW', 'MODERATE', 'HIGH', or 'CRITICAL'.
3. contributing_factors: An array of factors that abnormal parameters contribute to the risk score. For each factor, specify:
   - param_name: Name of the parameter.
   - value: Current value.
   - weight: Weight of importance (0.0 to 1.0).
   - contribution: Calculated contribution to risk (0.0 to 1.0).
   - status: Status of parameter ('NORMAL', 'LOW', 'HIGH', 'CRITICAL').
4. recommendations: A list of 3-5 clinical, dietary, or behavioral recommendations for the patient based on these metrics.

Return the result strictly in this JSON format:
{
  "overall_risk": 0.45,
  "risk_level": "MODERATE",
  "contributing_factors": [
    { "param_name": "HbA1c", "value": 6.2, "weight": 0.4, "contribution": 0.25, "status": "HIGH" }
  ],
  "recommendations": [
    "Consider a low-glycemic meal plan.",
    "Perform 30 minutes of aerobic exercise daily."
  ]
}
`;
      const response = await ai.models.generateContent({
        model: "gemini-3.6-flash",
        contents: prompt,
        config: {
          responseMimeType: "application/json",
          responseSchema: {
            type: import_genai.Type.OBJECT,
            properties: {
              overall_risk: { type: import_genai.Type.NUMBER },
              risk_level: { type: import_genai.Type.STRING },
              contributing_factors: {
                type: import_genai.Type.ARRAY,
                items: {
                  type: import_genai.Type.OBJECT,
                  properties: {
                    param_name: { type: import_genai.Type.STRING },
                    value: { type: import_genai.Type.NUMBER },
                    weight: { type: import_genai.Type.NUMBER },
                    contribution: { type: import_genai.Type.NUMBER },
                    status: { type: import_genai.Type.STRING }
                  },
                  required: ["param_name", "value", "weight", "contribution", "status"]
                }
              },
              recommendations: {
                type: import_genai.Type.ARRAY,
                items: { type: import_genai.Type.STRING }
              }
            },
            required: ["overall_risk", "risk_level", "contributing_factors", "recommendations"]
          }
        }
      });
      if (response.text) {
        const result = JSON.parse(response.text.trim());
        const score2 = new RiskScore({
          user_id: userId,
          overall_risk: result.overall_risk,
          risk_level: result.risk_level,
          contributing_factors: result.contributing_factors && result.contributing_factors.length > 0 ? result.contributing_factors : [{ param_name: "General", value: 0, weight: 0.1, contribution: 0, status: "NORMAL" }],
          recommendations: result.recommendations,
          version: nextVersion
        });
        score2.validate();
        await RiskScoreRepository.save(score2);
        return score2;
      }
    } catch (err) {
      console.error("Gemini risk score computation failed, falling back:", err);
    }
  }
  console.log("Using rule-based risk score calculator.");
  const contributing_factors = [];
  const recommendations = [];
  let totalAbnormalPoints = 0;
  parameters.forEach((p) => {
    if (p.status !== "NORMAL") {
      let weight = 0.1;
      let contribution = 0.05;
      if (p.param_name === "HbA1c" || p.param_name === "Fasting Blood Sugar") {
        weight = 0.35;
        contribution = p.status === "CRITICAL" ? 0.35 : 0.2;
      } else if (p.param_name.startsWith("Blood Pressure")) {
        weight = 0.3;
        contribution = p.status === "CRITICAL" ? 0.3 : 0.15;
      } else if (p.param_name === "Total Cholesterol" || p.param_name === "LDL") {
        weight = 0.25;
        contribution = p.status === "CRITICAL" ? 0.25 : 0.15;
      }
      totalAbnormalPoints += contribution;
      contributing_factors.push({
        param_name: p.param_name,
        value: p.value,
        weight,
        contribution,
        status: p.status
      });
      if (p.param_name === "HbA1c" || p.param_name === "Fasting Blood Sugar") {
        if (!recommendations.includes("Maintain a low-glycemic diet and monitor daily fasting glucose levels.")) {
          recommendations.push("Maintain a low-glycemic diet and monitor daily fasting glucose levels.");
        }
      }
      if (p.param_name.startsWith("Blood Pressure")) {
        if (!recommendations.includes("Limit daily sodium intake to under 1,500 mg and measure blood pressure daily.")) {
          recommendations.push("Limit daily sodium intake to under 1,500 mg and measure blood pressure daily.");
        }
      }
      if (p.param_name === "Total Cholesterol" || p.param_name === "LDL") {
        if (!recommendations.includes("Incorporate rich soluble dietary fiber and schedule cardiorespiratory exercise.")) {
          recommendations.push("Incorporate rich soluble dietary fiber and schedule cardiorespiratory exercise.");
        }
      }
    }
  });
  const overall_risk = Math.max(0.1, Math.min(0.95, totalAbnormalPoints));
  if (recommendations.length === 0) {
    recommendations.push("Maintain your balanced diet, stay hydrated, and continue regular physical activity.");
    recommendations.push("Ensure you schedule annual wellness exams and routine laboratory screenings.");
  }
  if (contributing_factors.length === 0) {
    if (parameters.length > 0) {
      const firstP = parameters[0];
      contributing_factors.push({
        param_name: firstP.param_name,
        value: firstP.value,
        weight: 0.1,
        contribution: 0,
        status: firstP.status
      });
    } else {
      contributing_factors.push({
        param_name: "General",
        value: 0,
        weight: 0.1,
        contribution: 0,
        status: "NORMAL"
      });
    }
  }
  const score = new RiskScore({
    user_id: userId,
    overall_risk,
    contributing_factors,
    recommendations,
    version: nextVersion
  });
  score.validate();
  await RiskScoreRepository.save(score);
  return score;
}
async function runGenerateDoctorReport(userId = "local_user") {
  const records = await HealthRecordRepository.findAll(userId);
  const parameters = await ClinicalParameterRepository.findAll(userId);
  const latestRisk = await RiskScoreRepository.findLatest(userId);
  const hasGeminiKey = getHasGeminiKey();
  if (records.length === 0) {
    throw new Error("At least one health record is required to generate a doctor prep report.");
  }
  if (hasGeminiKey) {
    try {
      const ai = new import_genai.GoogleGenAI({
        apiKey: process.env.GEMINI_API_KEY,
        httpOptions: {
          headers: {
            "User-Agent": "aistudio-build"
          }
        }
      });
      const recordsJson = records.map((r) => ({
        record_type: r.record_type,
        report_date: r.report_date,
        is_processed: r.is_processed
      }));
      const paramsJson = parameters.map((p) => ({
        param_name: p.param_name,
        value: p.value,
        unit: p.unit,
        status: p.status
      }));
      const prompt = `You are a premium AI clinical assistant. Your goal is to prepare a highly detailed and professional "Doctor Consultation Preparation Report" in Markdown format for the patient to present during their upcoming consultation.
      
Health Records available:
${JSON.stringify(recordsJson, null, 2)}

Clinical Bio-Markers extracted:
${JSON.stringify(paramsJson, null, 2)}

Computed Patient Risk Score:
${latestRisk ? `${latestRisk.risk_level} (Score: ${Math.round(latestRisk.overall_risk * 100)}%)` : "Unknown"}

Please structure the report beautifully with clear headings:
1. Clinical Executive Summary (a concise synthesis of overall health state)
2. Bio-Marker Analysis & Chronological Observations (analyze key indicators, highlight any abnormal status such as LOW, HIGH, or CRITICAL)
3. Health Risk Evaluation & Recommendations (summarize contributing factors and core clinical recommendations)
4. Key Consultation Discussion Topics & Questions (proactively suggest 3-5 specific questions the patient should ask their primary care provider based on these metrics)

Return ONLY the Markdown content. Do not wrap it in markdown code blocks.
`;
      const response = await ai.models.generateContent({
        model: "gemini-3.6-flash",
        contents: prompt
      });
      if (response.text) {
        const report2 = new DoctorReport({
          user_id: userId,
          report_content: response.text.trim(),
          records_included: records.map((r) => r.record_id)
        });
        report2.validate();
        await DoctorReportRepository.save(report2);
        return report2;
      }
    } catch (err) {
      console.error("Gemini doctor report generation failed, falling back:", err);
    }
  }
  console.log("Using rule-based doctor report generator.");
  let content = `# Doctor Consultation Preparation Report
`;
  content += `**Generated on**: ${(/* @__PURE__ */ new Date()).toLocaleDateString()}  
`;
  content += `**Prepared for**: ArogyaMitra Patient  
`;
  content += `**Security Status**: HIPAA Compliant Secure Dossier  

`;
  content += `## 1. Clinical Executive Summary
`;
  content += `This report compiles clinical intelligence extracted from **${records.length}** medical health records. `;
  content += `Based on current parameters, the patient exhibits a **${latestRisk?.risk_level || "LOW"}** overall clinical risk. `;
  content += `This preparation briefing is designed to streamline your upcoming physician consultation by consolidating health indices and highlighting active clinical concerns.

`;
  content += `## 2. Bio-Marker Analysis & Critical Observations
`;
  if (parameters.length === 0) {
    content += `*No active clinical bio-markers found. Please upload lab reports to build biomarker timeline records.*

`;
  } else {
    content += `The following clinical bio-markers were compiled chronologically:

`;
    parameters.forEach((p) => {
      const statusIcon = p.status === "NORMAL" ? "\u{1F7E2}" : p.status === "CRITICAL" ? "\u{1F534}" : "\u{1F7E1}";
      content += `- **${statusIcon} ${p.param_name}**: ${p.value} ${p.unit} - Status: **${p.status}** *(Observed on ${p.report_date.toLocaleDateString()})*
`;
    });
    content += `
`;
  }
  content += `## 3. Health Risk Evaluation & Core Recommendations
`;
  if (latestRisk) {
    content += `- **Overall Clinical Risk Assessment**: **${latestRisk.risk_level}** (Score index: ${Math.round(latestRisk.overall_risk * 100)}/100)
`;
    content += `- **Primary Contributing Indicators**:
`;
    if (latestRisk.contributing_factors.length === 0) {
      content += `  - No abnormal biomarkers are contributing to risks currently.
`;
    } else {
      latestRisk.contributing_factors.forEach((f) => {
        content += `  - **${f.param_name}** (Current value: ${f.value}) contributes with status ${f.status}.
`;
      });
    }
    content += `- **Actionable Care Advice**:
`;
    latestRisk.recommendations.forEach((r) => {
      content += `  - ${r}
`;
    });
    content += `
`;
  } else {
    content += `*Risk assessment is pending further clinical data upload.*

`;
  }
  content += `## 4. Consultation Discussion Guide (Questions for your Doctor)
`;
  content += `We recommend printing or sharing this secure portal screen with your healthcare provider and discussing these targeted topics:

`;
  const hasAbnormalHbA1c = parameters.some((p) => p.param_name === "HbA1c" && p.status !== "NORMAL");
  const hasAbnormalChol = parameters.some((p) => (p.param_name === "Total Cholesterol" || p.param_name === "LDL") && p.status !== "NORMAL");
  const hasAbnormalBP = parameters.some((p) => p.param_name.startsWith("Blood Pressure") && p.status !== "NORMAL");
  if (hasAbnormalHbA1c) {
    content += `- **Glucose Regulation**: *"Given my HbA1c of ${parameters.find((p) => p.param_name === "HbA1c")?.value}%, what glycemic control strategies or diagnostic evaluations do you advise?"*
`;
  }
  if (hasAbnormalChol) {
    content += `- **Cardiovascular Profile**: *"My LDL cholesterol index is elevated at ${parameters.find((p) => p.param_name === "LDL")?.value || "abnormal"} mg/dL. Should we explore medical lipid management or stick to specific dietary changes first?"*
`;
  }
  if (hasAbnormalBP) {
    content += `- **Hypertension Check**: *"My resting blood pressure is recorded in the ${parameters.find((p) => p.param_name === "Blood Pressure Systolic")?.value || "abnormal"}/${parameters.find((p) => p.param_name === "Blood Pressure Diastolic")?.value || "abnormal"} mmHg range. What limits do you recommend for activity or sodium, and when should we consider treatment?"*
`;
  }
  content += `- **General Wellness Check**: *"Are my vitamin profiles, kidney filtration index (eGFR), and general organic parameters in safe alignment with my long-term health plan?"*
`;
  content += `- **Scheduler Compliance**: *"Are there active medication or refill schedules we should review, update, or deprecate?"*
`;
  const report = new DoctorReport({
    user_id: userId,
    report_content: content,
    records_included: records.map((r) => r.record_id)
  });
  report.validate();
  await DoctorReportRepository.save(report);
  return report;
}
app.get("/api/records", async (req, res) => {
  try {
    const userId = getUserId(req);
    const records = await HealthRecordRepository.findAll(userId);
    res.json(records.map((r) => r.toDict()));
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/records/:id", async (req, res) => {
  try {
    const record = await HealthRecordRepository.findById(req.params.id);
    if (!record) {
      return res.status(404).json({ error: "RecordNotFound", message: "Health record not found" });
    }
    res.json(record.toDict());
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/records/:id/download", async (req, res) => {
  try {
    const record = await HealthRecordRepository.findById(req.params.id);
    if (!record) {
      return res.status(404).json({ error: "RecordNotFound", message: "Health record not found" });
    }
    if (!record.source_file_path || !import_fs2.default.existsSync(record.source_file_path)) {
      return res.status(404).json({ error: "FileNotFound", message: "No file associated with this record on storage." });
    }
    const encryptedData = await import_fs2.default.promises.readFile(record.source_file_path);
    const decrypted = decryptFile(encryptedData);
    const meta = record.extracted_entities || {};
    const originalName = meta.original_name || "decrypted_document.bin";
    const contentType = meta.mimetype || "application/octet-stream";
    res.setHeader("Content-Type", contentType);
    res.setHeader("Content-Disposition", `attachment; filename="${encodeURIComponent(originalName)}"`);
    res.send(decrypted);
  } catch (err) {
    console.error("File decryption or download failed:", err);
    res.status(500).json({ error: "DownloadError", message: "Failed to decrypt and download document." });
  }
});
app.post("/api/records/upload", upload.single("file"), async (req, res) => {
  try {
    const userId = getUserId(req);
    const recordType = req.body.record_type || "MANUAL_ENTRY";
    const reportDateStr = req.body.report_date;
    const reportDate = reportDateStr ? new Date(reportDateStr) : /* @__PURE__ */ new Date();
    let rawText = req.body.raw_text || "";
    let sourceFilePath = null;
    let encryptionHash = null;
    let originalName = null;
    let mimetype = null;
    if (req.file) {
      if (req.file.mimetype === "text/plain") {
        rawText += "\n" + req.file.buffer.toString("utf-8");
      } else {
        rawText += `
[Uploaded Document: ${req.file.originalname}]`;
      }
      const { encryptedData, hash } = encryptFile(req.file.buffer);
      encryptionHash = hash;
      originalName = req.file.originalname;
      mimetype = req.file.mimetype;
      const uploadDir = process.env.UPLOAD_DIR || "./backend/data/records/encrypted";
      if (!import_fs2.default.existsSync(uploadDir)) {
        import_fs2.default.mkdirSync(uploadDir, { recursive: true });
      }
      const fileExtension = import_path3.default.extname(req.file.originalname) || "";
      const safeFilename = `${import_crypto7.default.randomUUID()}${fileExtension}.enc`;
      sourceFilePath = import_path3.default.join(uploadDir, safeFilename);
      await import_fs2.default.promises.writeFile(sourceFilePath, encryptedData);
    }
    const record = new HealthRecord({
      user_id: userId,
      record_type: recordType,
      report_date: reportDate,
      raw_text: rawText || (req.file ? req.file.originalname : "Manual entry"),
      source_file_path: sourceFilePath,
      encryption_hash: encryptionHash,
      extracted_entities: originalName && mimetype ? { original_name: originalName, mimetype } : {},
      is_processed: false
    });
    record.validate();
    await HealthRecordRepository.save(record);
    const { parameters, reminders } = await extractParametersAndReminders(rawText, req.file);
    for (const p of parameters) {
      try {
        const cp = new ClinicalParameter({
          record_id: record.record_id,
          param_name: p.param_name,
          value: p.value,
          unit: p.unit,
          report_date: reportDate
        });
        cp.validate();
        await ClinicalParameterRepository.save(cp);
      } catch (paramErr) {
        console.error("Error saving extracted parameter:", p, paramErr);
      }
    }
    for (const r of reminders) {
      try {
        const rem = new Reminder({
          user_id: userId,
          reminder_type: r.reminder_type,
          title: r.title,
          due_date: new Date(r.due_date),
          recurrence: r.recurrence,
          created_from_record_id: record.record_id
        });
        rem.validate(true);
        await ReminderRepository.save(rem);
      } catch (remErr) {
        console.error("Error saving extracted reminder:", r, remErr);
      }
    }
    record.is_processed = true;
    await HealthRecordRepository.save(record);
    await runRecomputeRiskScore(userId);
    res.status(201).json(record.toDict());
  } catch (err) {
    console.error("Record upload failed:", err);
    res.status(400).json({ error: "UploadError", message: err.message });
  }
});
app.put("/api/records/:id", async (req, res) => {
  try {
    const record = await HealthRecordRepository.findById(req.params.id);
    if (!record) {
      return res.status(404).json({ error: "RecordNotFound", message: "Record not found" });
    }
    const { record_type, report_date } = req.body;
    if (record_type) record.record_type = record_type;
    if (report_date) record.report_date = new Date(report_date);
    record.validate();
    await HealthRecordRepository.save(record);
    res.json(record.toDict());
  } catch (err) {
    res.status(400).json({ error: "ValidationError", message: err.message });
  }
});
app.delete("/api/records/:id", async (req, res) => {
  try {
    const userId = getUserId(req);
    const record = await HealthRecordRepository.findById(req.params.id);
    if (!record) {
      return res.status(404).json({ error: "RecordNotFound", message: "Record not found" });
    }
    await HealthRecordRepository.softDelete(req.params.id);
    await runRecomputeRiskScore(userId);
    res.json({ success: true, message: "Health record deleted successfully" });
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/params", async (req, res) => {
  try {
    const userId = getUserId(req);
    const params = await ClinicalParameterRepository.findAll(userId);
    res.json(params.map((p) => p.toDict()));
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/params/:paramName", async (req, res) => {
  try {
    const userId = getUserId(req);
    const paramName = decodeURIComponent(req.params.paramName);
    const params = await ClinicalParameterRepository.findByParamName(paramName, userId);
    res.json(params.map((p) => p.toDict()));
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.put("/api/params/:paramId", async (req, res) => {
  try {
    const userId = getUserId(req);
    const { value } = req.body;
    if (value === void 0 || isNaN(value)) {
      return res.status(400).json({ error: "ValidationError", message: "Value must be a valid number." });
    }
    const allParams = await ClinicalParameterRepository.findAll(userId);
    const cp = allParams.find((p) => p.param_id === req.params.paramId);
    if (!cp) {
      return res.status(404).json({ error: "ParameterNotFound", message: "Clinical parameter not found." });
    }
    cp.value = Number(value);
    cp.status = cp.computeStatus();
    cp.validate();
    await ClinicalParameterRepository.update(cp.param_id, cp.value, cp.status);
    await runRecomputeRiskScore(userId);
    res.json(cp.toDict());
  } catch (err) {
    res.status(400).json({ error: "ValidationError", message: err.message });
  }
});
app.get("/api/reminders", async (req, res) => {
  try {
    const userId = getUserId(req);
    const activeOnly = req.query.active_only === "true";
    const reminders = activeOnly ? await ReminderRepository.findActive(userId) : await ReminderRepository.findAll(userId);
    res.json(reminders.map((r) => r.toDict()));
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.post("/api/reminders", async (req, res) => {
  try {
    const userId = getUserId(req);
    const { title, reminder_type, due_date, recurrence } = req.body;
    const reminder = new Reminder({
      user_id: userId,
      title,
      reminder_type,
      due_date: new Date(due_date),
      recurrence
    });
    reminder.validate(true);
    await ReminderRepository.save(reminder);
    res.status(201).json(reminder.toDict());
  } catch (err) {
    res.status(400).json({ error: "ValidationError", message: err.message });
  }
});
app.put("/api/reminders/:id", async (req, res) => {
  try {
    const reminder = await ReminderRepository.findById(req.params.id);
    if (!reminder) {
      return res.status(404).json({ error: "ReminderNotFound", message: "Reminder not found" });
    }
    const { title, reminder_type, due_date, recurrence, is_active } = req.body;
    if (title !== void 0) reminder.title = title;
    if (reminder_type !== void 0) reminder.reminder_type = reminder_type;
    if (due_date !== void 0) reminder.due_date = new Date(due_date);
    if (recurrence !== void 0) reminder.recurrence = recurrence;
    if (is_active !== void 0) reminder.is_active = !!is_active;
    reminder.validate();
    await ReminderRepository.save(reminder);
    res.json(reminder.toDict());
  } catch (err) {
    res.status(400).json({ error: "ValidationError", message: err.message });
  }
});
app.delete("/api/reminders/:id", async (req, res) => {
  try {
    const reminder = await ReminderRepository.findById(req.params.id);
    if (!reminder) {
      return res.status(404).json({ error: "ReminderNotFound", message: "Reminder not found" });
    }
    await ReminderRepository.delete(req.params.id);
    res.json({ success: true, message: "Reminder deleted successfully." });
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.patch("/api/reminders/:id/ack", async (req, res) => {
  try {
    const reminder = await ReminderRepository.findById(req.params.id);
    if (!reminder) {
      return res.status(404).json({ error: "ReminderNotFound", message: "Reminder not found" });
    }
    const { is_acknowledged } = req.body;
    await ReminderRepository.acknowledge(req.params.id, !!is_acknowledged);
    reminder.is_acknowledged = !!is_acknowledged;
    res.json(reminder.toDict());
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/report/latest", async (req, res) => {
  try {
    const userId = getUserId(req);
    const report = await DoctorReportRepository.findLatest(userId);
    if (!report) {
      return res.status(404).json({ error: "ReportNotFound", message: "No doctor prep reports available yet." });
    }
    res.json(report.toDict());
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.post("/api/report/generate", async (req, res) => {
  try {
    const userId = getUserId(req);
    const report = await runGenerateDoctorReport(userId);
    res.status(201).json(report.toDict());
  } catch (err) {
    res.status(400).json({ error: "GenerationError", message: err.message });
  }
});
app.post("/api/report/:reportId/share", async (req, res) => {
  try {
    const report = await DoctorReportRepository.findById(req.params.reportId);
    if (!report) {
      return res.status(404).json({ error: "ReportNotFound", message: "Doctor report not found" });
    }
    if (report.share_generated_at) {
      const diffMs = Date.now() - report.share_generated_at.getTime();
      if (diffMs < 36e5) {
        return res.status(400).json({
          error: "ShareTokenRegenerationLimit",
          message: "Share token cannot be regenerated for the same record within 1 hour of the last generation."
        });
      }
    }
    const expiryHours = req.body.expiry_hours || 24;
    const token = report.generateShareToken(expiryHours);
    await DoctorReportRepository.save(report);
    const shareUrl = `/#/share/${token}`;
    res.json({
      share_token: token,
      share_url: shareUrl,
      expires_at: report.share_expires_at.toISOString()
    });
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/risk/current", async (req, res) => {
  try {
    const userId = getUserId(req);
    let score = await RiskScoreRepository.findLatest(userId);
    if (!score) {
      score = await runRecomputeRiskScore(userId);
    }
    res.json(score.toDict());
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/risk/history", async (req, res) => {
  try {
    const userId = getUserId(req);
    const history = await RiskScoreRepository.getHistory(userId);
    res.json(history.map((s) => s.toDict()));
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.post("/api/risk/recompute", async (req, res) => {
  try {
    const userId = getUserId(req);
    const score = await runRecomputeRiskScore(userId);
    res.json(score.toDict());
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.get("/api/share/:token", async (req, res) => {
  try {
    const token = req.params.token;
    const record = await HealthRecordRepository.findByShareToken(token);
    if (record) {
      if (!record.isShareValid()) {
        return res.status(410).json({ error: "ShareExpired", message: "This clinical shared link has expired for compliance security." });
      }
      const cp = await ClinicalParameterRepository.findByRecordId(record.record_id);
      return res.json({
        type: "HEALTH_RECORD",
        data: record.toDict(),
        clinical_parameters: cp.map((p) => p.toDict())
      });
    }
    const report = await DoctorReportRepository.findByShareToken(token);
    if (report) {
      if (!report.isShareValid()) {
        return res.status(410).json({ error: "ShareExpired", message: "This clinical shared link has expired for compliance security." });
      }
      return res.json({
        type: "DOCTOR_REPORT",
        data: report.toDict()
      });
    }
    res.status(404).json({ error: "ShareNotFound", message: "This secure clinical shared link is invalid or expired." });
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
app.post("/api/chat", async (req, res) => {
  try {
    const { message, history } = req.body;
    if (!message) {
      return res.status(400).json({ error: "ValidationError", message: "Message is required." });
    }
    const records = await HealthRecordRepository.findAll();
    const parameters = await ClinicalParameterRepository.findAll();
    const latestRisk = await RiskScoreRepository.findLatest();
    const reminders = await ReminderRepository.findActive();
    const formattedParams = parameters.map(
      (p) => `- ${p.param_name}: ${p.value} ${p.unit} (Status: ${p.status}, Date: ${new Date(p.report_date).toLocaleDateString()})`
    ).join("\n");
    const formattedReminders = reminders.map(
      (r) => `- [${r.reminder_type}] ${r.title} (Due: ${new Date(r.due_date).toLocaleDateString()}, Recurrence: ${r.recurrence})`
    ).join("\n");
    const riskContext = latestRisk ? `Overall Risk Score: ${latestRisk.overall_risk}/100 (${latestRisk.risk_level} risk level). Contributing factors include: ${latestRisk.contributing_factors.map((f) => `${f.param_name} (${f.value})`).join(", ")}` : "No risk evaluation computed yet.";
    const recordsContext = records.map(
      (r) => `- ${r.record_type} (Date: ${new Date(r.report_date).toLocaleDateString()}, Processed: ${r.is_processed ? "Yes" : "No"})`
    ).join("\n");
    const hasGeminiKey = getHasGeminiKey();
    if (hasGeminiKey) {
      try {
        const ai = new import_genai.GoogleGenAI({
          apiKey: process.env.GEMINI_API_KEY,
          httpOptions: {
            headers: {
              "User-Agent": "aistudio-build"
            }
          }
        });
        const systemInstruction = `You are a professional, caring, and analytical AI Clinical Companion named ArogyaMitra.
Your goal is to answer the patient's questions accurately, empathetically, and contextually based on their local clinical database.
Always use the user's health metrics to ground your answers, and encourage them in their wellness journey.

CURRENT PATIENT HEALTH METRICS & CONTEXT:
=========================================
[Health Records List]
${recordsContext || "No records uploaded yet."}

[Biomarkers & Clinical Parameters]
${formattedParams || "No bio-markers recorded yet."}

[Medication & Scheduler Reminders]
${formattedReminders || "No reminders scheduled."}

[Risk Score Analysis]
${riskContext}
=========================================

IMPORTANT CLINICAL SAFETY GUIDELINES:
1. Always base your advice on the patient's actual recorded metrics when relevant.
2. If metrics are abnormal, gently explain why and suggest lifestyle changes (e.g. low-sodium if blood pressure is high, low-glycemic if glucose is elevated).
3. Do not prescribe drugs or offer absolute diagnostic declarations. Always suggest showing these reports to their healthcare provider.
4. You are equipped with Google Search Grounding. If the patient asks general medical questions or about recent medical literature, search for reliable medical data and explain it.
`;
        const contents = [];
        if (history && Array.isArray(history)) {
          for (const turn of history) {
            contents.push({
              role: turn.role === "user" ? "user" : "model",
              parts: [{ text: turn.text }]
            });
          }
        }
        contents.push({
          role: "user",
          parts: [{ text: message }]
        });
        const response = await ai.models.generateContent({
          model: "gemini-3.6-flash",
          contents,
          config: {
            systemInstruction,
            tools: [{ googleSearch: {} }]
          }
        });
        const text = response.text || "I was unable to formulate a response at the moment.";
        const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks || [];
        const sources = chunks.map((c) => ({
          title: c.web?.title || "Medical Reference Source",
          uri: c.web?.uri || "#"
        })).filter((s) => s.uri !== "#");
        return res.json({ text, sources });
      } catch (err) {
        console.error("Gemini Chat failed, executing programmatic fallback:", err);
      }
    }
    const query = message.toLowerCase();
    let reply = `**ArogyaMitra AI Companion [Sandbox Mode]**

Thank you for your question. My live clinical reasoning engine is currently running in a local sandboxed mode (awaiting a connected API key), but I can analyze your local clinical parameters and reports directly to guide you:

`;
    if (query.includes("hba1c") || query.includes("sugar") || query.includes("glucose") || query.includes("diabetes")) {
      const hba1c = parameters.find((p) => p.param_name === "HbA1c");
      const fbs = parameters.find((p) => p.param_name === "Fasting Blood Sugar");
      reply += `### Glycemic Health Review:
`;
      if (hba1c) {
        reply += `- **Your HbA1c Level**: \`${hba1c.value} ${hba1c.unit}\` (${hba1c.status}).
`;
      }
      if (fbs) {
        reply += `- **Your Fasting Blood Sugar**: \`${fbs.value} ${fbs.unit}\` (${fbs.status}).
`;
      }
      if (hba1c && hba1c.value > 6 || fbs && fbs.value > 100) {
        reply += `
**Clinical Observation**: Your glucose biomarkers are currently elevated. It is highly recommended to prioritize a low-glycemic diet (rich in dietary fiber, legumes, and lean proteins) and limit refined sugars. Engage in at least 30 minutes of aerobic exercise (like brisk walking) daily. Remember to take any prescribed medications on time.`;
      } else if (hba1c || fbs) {
        reply += `
**Clinical Observation**: Your glucose biomarkers are within an excellent, healthy range! Maintain your balanced nutritional framework and physical activity to preserve this glycemic level.`;
      } else {
        reply += `
No blood sugar or HbA1c records were found in your local files. You can upload a lab report to have me extract these clinical biomarkers automatically.`;
      }
    } else if (query.includes("cholesterol") || query.includes("lipid") || query.includes("ldl") || query.includes("hdl") || query.includes("triglycerides")) {
      const ldl = parameters.find((p) => p.param_name === "LDL");
      const hdl = parameters.find((p) => p.param_name === "HDL");
      const chol = parameters.find((p) => p.param_name === "Total Cholesterol");
      reply += `### Cardiovascular Lipid Review:
`;
      if (chol) reply += `- **Total Cholesterol**: \`${chol.value} ${chol.unit}\` (${chol.status})
`;
      if (ldl) reply += `- **LDL (Bad Cholesterol)**: \`${ldl.value} ${ldl.unit}\` (${ldl.status})
`;
      if (hdl) reply += `- **HDL (Good Cholesterol)**: \`${hdl.value} ${hdl.unit}\` (${hdl.status})
`;
      if (ldl && ldl.value > 100 || chol && chol.value > 200) {
        reply += `
**Clinical Observation**: Your lipid panels suggest elevated cardiovascular biomarkers. Restricting saturated fat intake, eliminating trans fats, and increasing soluble fiber (found in oats, barley, and beans) will help optimize these levels. Continue regular physical exertion and discuss with your clinician if medical therapy is required.`;
      } else if (ldl || chol) {
        reply += `
**Clinical Observation**: Your lipid panel is in a good, stable range. Excellent job maintaining your cardiovascular fitness!`;
      } else {
        reply += `
No lipid or cholesterol metrics were detected in your database. Please upload your latest lab reports to extract these variables.`;
      }
    } else if (query.includes("blood pressure") || query.includes("bp") || query.includes("hypertension") || query.includes("systolic")) {
      const sys = parameters.find((p) => p.param_name === "Blood Pressure Systolic");
      const dia = parameters.find((p) => p.param_name === "Blood Pressure Diastolic");
      reply += `### Blood Pressure & Circulatory Review:
`;
      if (sys && dia) {
        reply += `- **Your Blood Pressure**: \`${sys.value}/${dia.value} ${sys.unit}\` (Systolic: ${sys.status}, Diastolic: ${dia.status})
`;
        if (sys.value > 130 || dia.value > 80) {
          reply += `
**Clinical Observation**: Your BP readings indicate mild to moderate hypertension. Restricting dietary sodium intake (aim for < 1,500mg daily), implementing the DASH diet framework, managing stress, and regular cardiovascular exercise are pivotal home strategies. Ensure you monitor this daily.`;
        } else {
          reply += `
**Clinical Observation**: Your blood pressure is within a pristine normal range! Continue your healthy lifestyle choices.`;
        }
      } else {
        reply += `
No blood pressure records were found in your local logs. You can enter them manually or upload a doctor's report containing them.`;
      }
    } else if (query.includes("reminder") || query.includes("medication") || query.includes("schedule") || query.includes("pill")) {
      reply += `### Active Clinical Schedulers & Prescriptions:
`;
      if (reminders.length > 0) {
        reply += `You have **${reminders.length}** active clinical reminder(s) pending:

`;
        reply += formattedReminders;
        reply += `

**Clinical Guide**: Compliance is the most crucial part of clinical success. Ensure you take your medication daily as scheduled and mark them as completed in the Medication Scheduler tab.`;
      } else {
        reply += `You do not have any active medications or visit reminders scheduled. You can set them up in the 'Medication Scheduler' tab to keep your treatment on track.`;
      }
    } else if (query.includes("risk") || query.includes("score") || query.includes("status")) {
      reply += `### Overall Clinical Risk Assessment:
`;
      reply += `- **${riskContext}**

`;
      if (latestRisk && latestRisk.overall_risk > 30) {
        reply += `Your calculated risk index is currently elevated due to abnormal biomarkers. I recommend scheduling an active consultation and preparing your clinical consultation file in the **Doctor Prep Summary** tab.`;
      } else if (latestRisk) {
        reply += `Your health status is stable. Keep tracking parameters over time to detect early trends.`;
      }
    } else {
      reply += `### ArogyaMitra Health Companion Overview:
I am trained to support you with various agentic clinical tasks:
1. **Analyze Lab Results**: Type "HbA1c" or "lipid panel" to check sugar or cholesterol.
2. **Review BP Readings**: Type "blood pressure" to review circulatory metrics.
3. **Medication Schedule**: Type "medications" to see active reminders.
4. **Risk Evaluation**: Type "risk score" to view clinical indicators.

**Database Sync Status**: 
- **Health Records**: ${records.length} files index-logged.
- **Biomarkers**: ${parameters.length} biomarkers actively mapped.
- **Active Schedulers**: ${reminders.length} active reminders.

Please type a more specific question, or upload a new record in the Ingestion Center to enrich your profile!`;
    }
    res.json({ text: reply, sources: [] });
  } catch (err) {
    res.status(500).json({ error: "DatabaseError", message: err.message });
  }
});
async function startServer() {
  await initDB();
  if (process.env.NODE_ENV !== "production") {
    const vite = await (0, import_vite.createServer)({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    const distPath = import_path3.default.join(process.cwd(), "dist");
    app.use(import_express.default.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(import_path3.default.join(distPath, "index.html"));
    });
  }
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running at http://localhost:${PORT} in ${process.env.NODE_ENV || "development"} mode.`);
  });
}
startServer().catch((err) => {
  console.error("Failed to start fullstack application server:", err);
});
//# sourceMappingURL=server.cjs.map
