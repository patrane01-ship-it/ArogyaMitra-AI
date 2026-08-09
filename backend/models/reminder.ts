import crypto from 'crypto';
import { 
  EmptyReminderTitleError, 
  InvalidDueDateError, 
  InvalidRecurrenceError 
} from '../exceptions/arogya_errors.ts';

export type ReminderType = 'MEDICATION' | 'TEST_DUE' | 'DOCTOR_VISIT' | 'REFILL';
export type RecurrenceType = 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY';

export class Reminder {
  reminder_id: string;
  user_id: string;
  reminder_type: ReminderType;
  title: string;
  due_date: Date;
  recurrence: RecurrenceType;
  is_active: boolean;
  is_acknowledged: boolean;
  created_from_record_id: string | null;

  constructor(params: {
    reminder_id?: string;
    user_id?: string;
    reminder_type: ReminderType;
    title: string;
    due_date: Date;
    recurrence?: RecurrenceType;
    is_active?: boolean;
    is_acknowledged?: boolean;
    created_from_record_id?: string | null;
  }) {
    this.reminder_id = params.reminder_id || globalThis.crypto?.randomUUID() || crypto.randomUUID();
    this.user_id = params.user_id || 'local_user';
    this.reminder_type = params.reminder_type;
    this.title = params.title;
    this.due_date = params.due_date;
    this.recurrence = params.recurrence || 'NONE';
    this.is_active = params.is_active !== undefined ? params.is_active : true;
    this.is_acknowledged = params.is_acknowledged !== undefined ? params.is_acknowledged : false;
    this.created_from_record_id = params.created_from_record_id || null;
  }

  isDueToday(): boolean {
    const today = new Date();
    return (
      this.due_date.getDate() === today.getDate() &&
      this.due_date.getMonth() === today.getMonth() &&
      this.due_date.getFullYear() === today.getFullYear()
    );
  }

  validate(isNew: boolean = false): void {
    if (!this.title || this.title.trim().length < 3) {
      throw new EmptyReminderTitleError('Reminder title must be at least 3 characters long.');
    }

    const now = new Date();
    // For a brand new reminder, the due date must be in the future (with a small grace period)
    if (isNew && this.due_date.getTime() < now.getTime() - 60000) {
      throw new InvalidDueDateError(`Reminder due date cannot be in the past for new reminders. Got: ${this.due_date.toISOString()}`);
    }

    const twoYearsFromNow = new Date();
    twoYearsFromNow.setFullYear(twoYearsFromNow.getFullYear() + 2);
    if (this.due_date.getTime() > twoYearsFromNow.getTime()) {
      throw new InvalidDueDateError('Reminder due date cannot be more than 2 years in the future.');
    }

    const validRecurrences: RecurrenceType[] = ['NONE', 'DAILY', 'WEEKLY', 'MONTHLY'];
    if (!validRecurrences.includes(this.recurrence)) {
      throw new InvalidRecurrenceError(`Invalid recurrence value: ${this.recurrence}`);
    }

    const validTypes: ReminderType[] = ['MEDICATION', 'TEST_DUE', 'DOCTOR_VISIT', 'REFILL'];
    if (!validTypes.includes(this.reminder_type)) {
      throw new InvalidRecurrenceError(`Invalid reminder type value: ${this.reminder_type}`);
    }
  }

  toDict(): Record<string, any> {
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

  static fromDict(data: Record<string, any>): Reminder {
    return new Reminder({
      reminder_id: data.reminder_id,
      user_id: data.user_id,
      reminder_type: data.reminder_type as ReminderType,
      title: data.title,
      due_date: new Date(data.due_date),
      recurrence: data.recurrence as RecurrenceType,
      is_active: !!data.is_active,
      is_acknowledged: !!data.is_acknowledged,
      created_from_record_id: data.created_from_record_id
    });
  }
}
