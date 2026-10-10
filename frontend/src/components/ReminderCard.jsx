import React from 'react';
import { Bell, Check, Trash2, Calendar, Pill } from 'lucide-react';
import { formatDate } from '../utils/formatDate';

export default function ReminderCard({ reminder, onAcknowledge, onDelete }) {
  const isMedication = reminder.reminder_type === 'MEDICATION';

  return (
    <div
      className={`glass-card rounded-2xl p-4 border transition-all ${
        reminder.is_acknowledged
          ? 'bg-gray-50/70 border-gray-200 opacity-75'
          : reminder.is_due_today
          ? 'border-accent/80 shadow-sm bg-mint-50/20'
          : 'border-gray-200'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
              isMedication ? 'bg-teal-50 text-teal-700' : 'bg-purple-50 text-purple-700'
            }`}
          >
            {isMedication ? <Pill className="w-4 h-4" /> : <Calendar className="w-4 h-4" />}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                {reminder.reminder_type}
              </span>
              {reminder.recurrence !== 'NONE' && (
                <span className="text-[10px] font-medium text-gray-500">
                  {reminder.recurrence.toLowerCase()}
                </span>
              )}
            </div>

            <h4
              className={`text-sm font-semibold mt-1 text-gray-900 ${
                reminder.is_acknowledged ? 'line-through text-gray-500' : ''
              }`}
            >
              {reminder.title}
            </h4>

            <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
              <span>Due:</span>
              <strong className="text-gray-700 font-medium">
                {formatDate(reminder.due_date)}
              </strong>
              {reminder.is_due_today && (
                <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.2 rounded font-bold ml-1">
                  TODAY
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1.5 shrink-0">
          {!reminder.is_acknowledged && (
            <button
              onClick={() => onAcknowledge(reminder.reminder_id)}
              className="p-1.5 text-primary hover:bg-primary/10 rounded-lg transition-colors border border-primary/20"
              title="Acknowledge reminder"
            >
              <Check className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={() => onDelete(reminder.reminder_id)}
            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Delete reminder"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
