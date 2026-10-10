import React, { useState, useEffect } from 'react';
import { Activity, UploadCloud, Bell, FileText, ArrowRight, ShieldCheck } from 'lucide-react';
import RiskGauge from '../components/RiskGauge';
import RecordCard from '../components/RecordCard';
import ReminderCard from '../components/ReminderCard';
import {
  getCurrentRisk,
  recomputeRisk,
  getRecords,
  getReminders,
  acknowledgeReminder,
  deleteReminder,
  downloadRecord,
  deleteRecord,
} from '../services/api';

export default function DashboardPage({ setActivePage, setSelectedRecordId }) {
  const [riskData, setRiskData] = useState(null);
  const [records, setRecords] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRecomputing, setIsRecomputing] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [riskRes, recordsRes, remindersRes] = await Promise.allSettled([
        getCurrentRisk(),
        getRecords(0, 4),
        getReminders(false),
      ]);

      if (riskRes.status === 'fulfilled') setRiskData(riskRes.value);
      if (recordsRes.status === 'fulfilled') setRecords(recordsRes.value);
      if (remindersRes.status === 'fulfilled') setReminders(remindersRes.value.slice(0, 3));
    } catch (e) {
      console.error('Error fetching dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRecompute = async () => {
    setIsRecomputing(true);
    try {
      const updated = await recomputeRisk();
      setRiskData(updated);
    } catch (e) {
      console.error('Recompute failed:', e);
    } finally {
      setIsRecomputing(false);
    }
  };

  const handleAcknowledgeReminder = async (id) => {
    try {
      await acknowledgeReminder(id);
      setReminders((prev) => prev.filter((r) => r.reminder_id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteReminder = async (id) => {
    try {
      await deleteReminder(id);
      setReminders((prev) => prev.filter((r) => r.reminder_id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleDownloadRecord = async (recordId) => {
    try {
      const blob = await downloadRecord(recordId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `medical_record_${recordId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert('Failed to download record.');
    }
  };

  const handleDeleteRecord = async (recordId) => {
    if (!confirm('Are you sure you want to remove this record?')) return;
    try {
      await deleteRecord(recordId);
      setRecords((prev) => prev.filter((r) => r.record_id !== recordId));
      handleRecompute();
    } catch (e) {
      alert('Failed to delete record.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-medium text-gray-600">Gathering health intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome & Highlights Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-primary to-primary-dark text-white p-6 sm:p-8 rounded-3xl shadow-xl shadow-primary/10">
        <div>
          <span className="text-xs uppercase font-bold tracking-widest text-accent-light px-2.5 py-1 rounded-full bg-white/10 inline-block mb-2">
            Clinical Summary Overview
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Personal Health Intelligence
          </h1>
          <p className="text-sm text-teal-100/90 mt-1 max-w-xl">
            ArogyaMitra tracks clinical trajectories, flags multi-marker anomalies, and prepares structured pre-visit dossiers for your physician.
          </p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          <button
            onClick={() => setActivePage('upload')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-accent text-primary-dark font-bold text-xs sm:text-sm hover:bg-accent-light transition-all shadow-md"
          >
            <UploadCloud className="w-4 h-4" /> Upload Document
          </button>
          <button
            onClick={() => setActivePage('report')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium text-xs sm:text-sm border border-white/20 transition-all"
          >
            <FileText className="w-4 h-4" /> Doctor-Prep Report
          </button>
        </div>
      </div>

      {/* Main Grid: Gauge & Reminders */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Gauge Column */}
        <div className="lg:col-span-2">
          <RiskGauge
            riskData={riskData}
            onRecompute={handleRecompute}
            isRecomputing={isRecomputing}
          />
        </div>

        {/* Reminders Column */}
        <div className="glass-card rounded-2xl p-6 border border-gray-200/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-900 tracking-tight flex items-center gap-2">
                <Bell className="w-4 h-4 text-primary" /> Active Reminders
              </h3>
              <button
                onClick={() => setActivePage('reminders')}
                className="text-xs text-primary hover:underline font-semibold flex items-center gap-1"
              >
                View all <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {reminders.length === 0 ? (
              <div className="p-6 text-center text-xs text-gray-500 bg-gray-50 rounded-xl border border-gray-100">
                No active medication reminders today.
              </div>
            ) : (
              <div className="space-y-3">
                {reminders.map((r) => (
                  <ReminderCard
                    key={r.reminder_id}
                    reminder={r}
                    onAcknowledge={handleAcknowledgeReminder}
                    onDelete={handleDeleteReminder}
                  />
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => setActivePage('reminders')}
            className="w-full mt-4 py-2 text-xs font-semibold text-primary hover:bg-primary/5 rounded-xl border border-primary/20 transition-all text-center"
          >
            Manage All Medication Schedules
          </button>
        </div>
      </div>

      {/* Recent Records Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 tracking-tight">
              Recent Health Documents
            </h2>
            <p className="text-xs text-gray-500">
              Encrypted lab tests, prescriptions, and manual entries
            </p>
          </div>
          <button
            onClick={() => setActivePage('upload')}
            className="text-xs text-primary hover:underline font-semibold flex items-center gap-1"
          >
            Add new record <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {records.length === 0 ? (
          <div className="glass-card rounded-2xl p-8 text-center border-dashed border-2 border-gray-200">
            <ShieldCheck className="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-gray-700">No medical documents yet</h4>
            <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
              Upload your lab panels, prescriptions, or imaging reports to build your timeline.
            </p>
            <button
              onClick={() => setActivePage('upload')}
              className="mt-4 px-4 py-2 rounded-xl bg-primary text-white text-xs font-medium"
            >
              Upload Document
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {records.map((r) => (
              <RecordCard
                key={r.record_id}
                record={r}
                onDownload={handleDownloadRecord}
                onDelete={handleDeleteRecord}
                onViewDetails={(id) => {
                  setSelectedRecordId(id);
                  setActivePage('detail');
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
