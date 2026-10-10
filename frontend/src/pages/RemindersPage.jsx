import React, { useState, useEffect } from 'react';
import { Bell, Plus, Calendar, Pill, CheckCircle2, Clock } from 'lucide-react';
import ReminderCard from '../components/ReminderCard';
import {
  getReminders,
  createReminder,
  acknowledgeReminder,
  deleteReminder,
} from '../services/api';

export default function RemindersPage() {
  const [reminders, setReminders] = useState([]);
  const [includeAcknowledged, setIncludeAcknowledged] = useState(false);
  const [loading, setLoading] = useState(true);

  // New reminder modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [reminderType, setReminderType] = useState('MEDICATION');
  const [dueDate, setDueDate] = useState(new Date().toISOString().split('T')[0]);
  const [recurrence, setRecurrence] = useState('DAILY');
  const [submitting, setSubmitting] = useState(false);

  const fetchReminders = async () => {
    setLoading(true);
    try {
      const data = await getReminders(includeAcknowledged);
      setReminders(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
  }, [includeAcknowledged]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    setSubmitting(true);
    try {
      await createReminder({
        title,
        reminder_type: reminderType,
        due_date: new Date(dueDate).toISOString(),
        recurrence,
      });
      setTitle('');
      setShowAddModal(false);
      fetchReminders();
    } catch (err) {
      alert('Failed to create reminder: ' + (err.response?.data?.message || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await acknowledgeReminder(id);
      fetchReminders();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteReminder(id);
      setReminders((prev) => prev.filter((r) => r.reminder_id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2">
            <Bell className="w-6 h-6 text-primary" /> Medication & Health Reminders
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Auto-extracted prescription dosages, refill dates, and follow-up clinical tests
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary hover:bg-primary-dark text-white font-semibold text-xs sm:text-sm shadow-md shadow-primary/20 transition-all"
        >
          <Plus className="w-4 h-4" /> Add Reminder
        </button>
      </div>

      {/* Filter toggle */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-3">
        <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={includeAcknowledged}
            onChange={(e) => setIncludeAcknowledged(e.target.checked)}
            className="rounded text-primary focus:ring-primary"
          />
          <span>Show acknowledged & completed reminders</span>
        </label>
        <span className="text-xs text-gray-400 font-medium">
          {reminders.length} reminder{reminders.length === 1 ? '' : 's'}
        </span>
      </div>

      {/* Reminders List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-gray-500">
          Loading reminder schedules...
        </div>
      ) : reminders.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center border-dashed border-2 border-gray-200">
          <Pill className="w-10 h-10 text-gray-300 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-gray-700">No active schedules</h4>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            Upload a prescription to automatically extract medications or add custom schedules manually.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {reminders.map((r) => (
            <ReminderCard
              key={r.reminder_id}
              reminder={r}
              onAcknowledge={handleAcknowledge}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Add Reminder Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-200">
            <h3 className="text-base font-bold text-gray-900 mb-4">
              Schedule New Reminder
            </h3>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Reminder Title / Medication
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Metformin 500mg after dinner"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full text-xs rounded-xl border border-gray-300 p-2.5 focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={reminderType}
                    onChange={(e) => setReminderType(e.target.value)}
                    className="w-full text-xs rounded-xl border border-gray-300 p-2.5 bg-white"
                  >
                    <option value="MEDICATION">Medication (Rx)</option>
                    <option value="TEST_DUE">Lab Test Due</option>
                    <option value="DOCTOR_VISIT">Doctor Visit</option>
                    <option value="REFILL">Prescription Refill</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Recurrence
                  </label>
                  <select
                    value={recurrence}
                    onChange={(e) => setRecurrence(e.target.value)}
                    className="w-full text-xs rounded-xl border border-gray-300 p-2.5 bg-white"
                  >
                    <option value="NONE">Once (None)</option>
                    <option value="DAILY">Daily</option>
                    <option value="WEEKLY">Weekly</option>
                    <option value="MONTHLY">Monthly</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Due Date
                </label>
                <input
                  type="date"
                  required
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full text-xs rounded-xl border border-gray-300 p-2.5"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-primary hover:bg-primary-dark rounded-xl shadow-md"
                >
                  {submitting ? 'Saving...' : 'Create Reminder'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
