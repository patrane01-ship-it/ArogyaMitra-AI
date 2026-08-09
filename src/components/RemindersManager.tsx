import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Calendar, 
  Clock, 
  Plus, 
  Trash2, 
  Check, 
  X, 
  AlertTriangle, 
  Clipboard, 
  ToggleLeft, 
  CheckSquare 
} from 'lucide-react';
import { api } from '../services/api.ts';
import { Reminder, ReminderType, RecurrenceType } from '../types.ts';

export const RemindersManager: React.FC = () => {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  
  // New Reminder form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [title, setTitle] = useState('');
  const [reminderType, setReminderType] = useState<ReminderType>('MEDICATION');
  const [dueDate, setDueDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [recurrence, setRecurrence] = useState<RecurrenceType>('NONE');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchReminders = async () => {
    try {
      const data = await api.getReminders(false); // get ALL reminders (including acknowledged)
      // Sort so active & unacknowledged ones are at the top, then sorted by due_date ASC
      const sorted = [...data].sort((a, b) => {
        if (a.is_acknowledged !== b.is_acknowledged) {
          return a.is_acknowledged ? 1 : -1; // unacknowledged first
        }
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      });
      setReminders(sorted);
    } catch (err) {
      console.error('Failed to fetch reminders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
  }, []);

  const handleAckToggle = async (id: string, currentlyAcked: boolean) => {
    try {
      await api.acknowledgeReminder(id, !currentlyAcked);
      setReminders(prev => 
        prev.map(r => r.reminder_id === id ? { ...r, is_acknowledged: !currentlyAcked } : r)
      );
    } catch (err: any) {
      alert('Failed to update reminder: ' + err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to remove this reminder?')) return;
    try {
      await api.deleteReminder(id);
      setReminders(prev => prev.filter(r => r.reminder_id !== id));
    } catch (err: any) {
      alert('Failed to delete reminder: ' + err.message);
    }
  };

  const handleCreateReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setFormError('Please provide a descriptive reminder title.');
      return;
    }

    // Set time to 9 AM local
    const combinedDate = new Date(dueDate);
    combinedDate.setHours(9, 0, 0, 0);

    setIsSubmitting(true);
    setFormError(null);

    try {
      const newRem = await api.createReminder({
        title,
        reminder_type: reminderType,
        due_date: combinedDate.toISOString(),
        recurrence
      });
      
      setReminders(prev => [newRem, ...prev]);
      setTitle('');
      setRecurrence('NONE');
      setShowAddForm(false);
    } catch (err: any) {
      setFormError(err.message || 'Failed to create reminder.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Groupings for display
  const activeReminders = reminders.filter(r => !r.is_acknowledged);
  const completedReminders = reminders.filter(r => r.is_acknowledged);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8" id="reminders-manager-view">
      
      {/* Left Panel: Medication Schedules */}
      <div className="lg:col-span-8 space-y-6">
        <div className="flex justify-between items-center bg-white p-6 border border-gray-100 rounded-xl shadow-sm">
          <div>
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Clock className="w-5 h-5 text-teal-600" />
              Schedules & Medication Intake
            </h2>
            <p className="text-sm text-gray-500 mt-1">Check medication intakes and monitor test schedules.</p>
          </div>
          
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-teal-700 text-white font-semibold rounded-lg hover:bg-teal-800 transition flex items-center gap-1.5 shadow-sm text-sm"
            id="btn-toggle-add-reminder"
          >
            <Plus className="w-4 h-4" />
            Add Reminder
          </button>
        </div>

        {loading ? (
          <div className="bg-white border border-gray-100 rounded-xl p-20 flex justify-center items-center">
            <Clock className="w-8 h-8 text-teal-600 animate-spin" />
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* Active Reminders List */}
            <div>
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Due Today / Upcoming</h3>
              {activeReminders.length > 0 ? (
                <div className="space-y-3">
                  {activeReminders.map((rem) => (
                    <div 
                      key={rem.reminder_id} 
                      className="p-4 rounded-xl border border-gray-200 bg-white shadow-sm flex items-center justify-between hover:border-teal-200 transition"
                    >
                      <div className="flex items-center gap-4">
                        <button 
                          onClick={() => handleAckToggle(rem.reminder_id, rem.is_acknowledged)}
                          className="w-6 h-6 rounded-lg border border-gray-300 hover:border-teal-500 bg-white flex items-center justify-center transition-all shadow-sm"
                          title="Complete/Take Medication"
                          id={`btn-ack-reminder-${rem.reminder_id}`}
                        >
                          <span className="text-xs text-white group-hover:text-teal-600"></span>
                        </button>
                        
                        <div>
                          <p className="text-sm font-semibold text-gray-800">{rem.title}</p>
                          <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                            <Calendar className="w-3.5 h-3.5" />
                            Due: {new Date(rem.due_date).toLocaleDateString()}
                            {rem.recurrence !== 'NONE' && (
                              <span className="bg-teal-50 text-teal-700 px-1.5 py-0.2 rounded text-[10px] font-bold uppercase ml-1.5">
                                {rem.recurrence}
                              </span>
                            )}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          rem.reminder_type === 'MEDICATION' 
                            ? 'bg-teal-50 text-teal-700' 
                            : rem.reminder_type === 'DOCTOR_VISIT'
                            ? 'bg-indigo-50 text-indigo-700'
                            : 'bg-yellow-50 text-yellow-700'
                        }`}>
                          {rem.reminder_type}
                        </span>

                        <button
                          onClick={() => handleDelete(rem.reminder_id)}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                          title="Remove reminder"
                          id={`btn-delete-reminder-${rem.reminder_id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-white border border-dashed border-gray-200 rounded-xl p-12 text-center text-gray-500">
                  <CheckSquare className="w-10 h-10 text-teal-100 mx-auto mb-3" />
                  <p className="text-sm font-semibold text-gray-700">All caught up!</p>
                  <p className="text-xs text-gray-400 mt-1">You have no pending medications or scheduled tasks.</p>
                </div>
              )}
            </div>

            {/* Completed Log */}
            {completedReminders.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Taken / Completed Log</h3>
                <div className="space-y-2">
                  {completedReminders.map((rem) => (
                    <div 
                      key={rem.reminder_id} 
                      className="p-3.5 rounded-xl border border-gray-100 bg-gray-50/50 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={() => handleAckToggle(rem.reminder_id, rem.is_acknowledged)}
                          className="w-5 h-5 rounded-md bg-teal-600 text-white flex items-center justify-center transition-colors shadow-sm"
                          title="Mark untaken"
                          id={`btn-unack-reminder-${rem.reminder_id}`}
                        >
                          <Check className="w-3.5 h-3.5 font-bold" />
                        </button>
                        <div>
                          <p className="text-xs font-semibold text-gray-500 line-through">{rem.title}</p>
                          <p className="text-[10px] text-gray-400 mt-0.5">Checked off successfully</p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDelete(rem.reminder_id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg transition"
                        id={`btn-delete-completed-${rem.reminder_id}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
      </div>

      {/* Right Panel: Add Form Or Instructions */}
      <div className="lg:col-span-4">
        <AnimatePresence mode="wait">
          {showAddForm ? (
            /* Custom Form */
            <motion.div 
              key="form"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 15 }}
              className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm space-y-6"
              id="add-reminder-form"
            >
              <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wider">New Clinical Reminder</h3>
                <button 
                  onClick={() => setShowAddForm(false)} 
                  className="text-gray-400 hover:text-gray-600"
                  id="btn-close-form"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {formError && (
                <div className="bg-red-50 border border-red-100 text-red-800 p-3 rounded-lg text-xs flex gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <form onSubmit={handleCreateReminder} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Reminder Action Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Take Metformin 500mg - Once Daily"
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500"
                    id="input-reminder-title"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Schedule Type</label>
                  <select
                    value={reminderType}
                    onChange={(e) => setReminderType(e.target.value as ReminderType)}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500"
                    id="select-reminder-type"
                  >
                    <option value="MEDICATION">Medication Intake</option>
                    <option value="TEST_DUE">Due Medical Lab Test</option>
                    <option value="DOCTOR_VISIT">Doctor Appointment</option>
                    <option value="REFILL">Prescription Refill Order</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Due Date</label>
                  <input
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500"
                    id="input-reminder-due-date"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Recurrence Frequency</label>
                  <select
                    value={recurrence}
                    onChange={(e) => setRecurrence(e.target.value as RecurrenceType)}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500"
                    id="select-reminder-recurrence"
                  >
                    <option value="NONE">One-Time (No Recurrence)</option>
                    <option value="DAILY">Daily Schedule</option>
                    <option value="WEEKLY">Weekly Schedule</option>
                    <option value="MONTHLY">Monthly Schedule</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold rounded-lg transition disabled:opacity-50 shadow-sm"
                  id="btn-reminder-submit"
                >
                  {isSubmitting ? 'Scheduling...' : 'Confirm Schedule'}
                </button>
              </form>
            </motion.div>
          ) : (
            /* Educational Panel */
            <motion.div 
              key="guide"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-teal-50/50 border border-teal-100 rounded-xl p-6 shadow-sm space-y-4"
              id="reminder-helper-card"
            >
              <h3 className="font-bold text-teal-900 text-sm uppercase tracking-wider flex items-center gap-1.5">
                <Clipboard className="w-4 h-4 text-teal-700" />
                Prescription Parsing
              </h3>
              <p className="text-xs text-teal-800 leading-relaxed">
                When you upload a clinical <strong>Doctor Prescription</strong> in the Ingestion Center, ArogyaMitra AI automatically identifies scheduled medications, instructions, and follow-ups.
              </p>
              <p className="text-xs text-teal-800 leading-relaxed">
                Those items are instantly written directly into this reminder center as scheduled tasks. This eliminates medication errors and missed lab followups!
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

    </div>
  );
};
