import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { 
  Activity, 
  AlertTriangle, 
  Calendar, 
  CheckCircle, 
  Clock, 
  FileText, 
  TrendingUp, 
  ShieldCheck, 
  RefreshCw 
} from 'lucide-react';
import { api } from '../services/api.ts';
import { RiskScore, Reminder, HealthRecord } from '../types.ts';

interface DashboardProps {
  onNavigate: (tab: string) => void;
  onSelectRecord: (recordId: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate, onSelectRecord }) => {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      const [latestRisk, activeReminders, allRecords] = await Promise.all([
        api.getLatestRiskScore(),
        api.getReminders(true),
        api.getRecords()
      ]);
      setRiskScore(latestRisk);
      setReminders(activeReminders.slice(0, 5)); // show top 5 active reminders
      setRecords(allRecords.slice(0, 3)); // show top 3 recent records
      setError(null);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load health metrics. Ensure server is active.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRecomputeRisk = async () => {
    setRefreshing(true);
    try {
      const freshRisk = await api.recomputeRiskScore();
      setRiskScore(freshRisk);
    } catch (err: any) {
      alert('Recomputation failed: ' + err.message);
    } finally {
      setRefreshing(false);
    }
  };

  const handleAckReminder = async (id: string, currentlyAcked: boolean) => {
    try {
      await api.acknowledgeReminder(id, !currentlyAcked);
      // update state
      setReminders(prev => 
        prev.map(r => r.reminder_id === id ? { ...r, is_acknowledged: !currentlyAcked } : r)
      );
    } catch (err: any) {
      alert('Failed to update reminder: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <RefreshCw className="w-10 h-10 text-teal-600 animate-spin mb-4" id="loading-spinner" />
        <p className="text-gray-600 font-medium">Assembling your medical dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 p-6 rounded-xl flex flex-col items-center text-center max-w-lg mx-auto my-12" id="dashboard-error">
        <AlertTriangle className="w-12 h-12 text-red-600 mb-3" />
        <h3 className="text-lg font-bold mb-1">Connection Error</h3>
        <p className="text-sm text-red-700 mb-4">{error}</p>
        <button 
          onClick={() => { setLoading(true); fetchDashboardData(); }}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  // Determine risk meter color parameters
  const riskPercent = riskScore ? Math.round(riskScore.overall_risk * 100) : 0;
  let riskColorClass = 'text-green-600 bg-green-50 border-green-200';
  let strokeColor = '#10B981'; // Green
  if (riskScore?.risk_level === 'MODERATE') {
    riskColorClass = 'text-yellow-600 bg-yellow-50 border-yellow-200';
    strokeColor = '#F59E0B'; // Yellow
  } else if (riskScore?.risk_level === 'HIGH') {
    riskColorClass = 'text-orange-600 bg-orange-50 border-orange-200';
    strokeColor = '#F97316'; // Orange
  } else if (riskScore?.risk_level === 'CRITICAL') {
    riskColorClass = 'text-red-600 bg-red-50 border-red-200';
    strokeColor = '#EF4444'; // Red
  }

  // Gauge parameters
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (riskPercent / 100) * circumference;

  return (
    <div className="space-y-8" id="dashboard-view">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-teal-50 border border-teal-100 rounded-xl p-6">
        <div>
          <h2 className="text-2xl font-bold text-teal-900 font-serif">Welcome to ArogyaMitra AI</h2>
          <p className="text-teal-700 mt-1 max-w-xl">
            Your secure personal health intelligence system. Upload reports, track your bio-markers, and build a synthesized clinical pre-visit summary.
          </p>
        </div>
        <button 
          onClick={() => onNavigate('upload')}
          className="px-5 py-2.5 bg-teal-700 text-white font-semibold rounded-lg hover:bg-teal-800 transition flex items-center gap-2 shadow-sm"
          id="btn-quick-upload"
        >
          <FileText className="w-4 h-4" />
          Upload New Record
        </button>
      </div>

      {/* Grid: Risk Score Card & Quick Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Risk Gauge Panel */}
        <div className="lg:col-span-5 bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between" id="risk-score-card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <Activity className="w-5 h-5 text-teal-600" />
              Health Risk Evaluation
            </h3>
            <button 
              onClick={handleRecomputeRisk} 
              disabled={refreshing}
              className="text-gray-500 hover:text-teal-600 transition disabled:opacity-50 p-1 rounded-full hover:bg-gray-50"
              title="Recalculate risk analysis"
              id="btn-recompute-risk"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-teal-600' : ''}`} />
            </button>
          </div>

          <div className="flex flex-col items-center py-6">
            <div className="relative w-36 h-36 flex items-center justify-center">
              {/* Circular gauge SVG */}
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="72"
                  cy="72"
                  r={radius}
                  className="stroke-gray-100"
                  strokeWidth="10"
                  fill="transparent"
                />
                <circle
                  cx="72"
                  cy="72"
                  r={radius}
                  stroke={strokeColor}
                  strokeWidth="10"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-3xl font-extrabold text-gray-900">{riskPercent}%</span>
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 mt-0.5">Overall Risk</span>
              </div>
            </div>

            <div className={`mt-6 px-4 py-1.5 rounded-full border text-xs font-bold tracking-wider uppercase ${riskColorClass}`}>
              {riskScore?.risk_level} Risk Level
            </div>
          </div>

          {/* Contributing parameters if any */}
          <div className="border-t border-gray-100 pt-4 mt-4">
            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Key Impact Markers</h4>
            {riskScore && riskScore.contributing_factors.length > 0 ? (
              <div className="space-y-3">
                {riskScore.contributing_factors.slice(0, 3).map((factor, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <span className="text-gray-700 font-medium">{factor.param_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Value: {factor.value}</span>
                      <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                        factor.status === 'CRITICAL' ? 'bg-red-50 text-red-700' : 'bg-orange-50 text-orange-700'
                      }`}>
                        {factor.status}
                      </span>
                    </div>
                  </div>
                ))}
                {riskScore.contributing_factors.length > 3 && (
                  <button 
                    onClick={() => onNavigate('timeline')}
                    className="text-xs font-bold text-teal-600 hover:text-teal-700 mt-1 block"
                  >
                    View all {riskScore.contributing_factors.length} impact markers →
                  </button>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">No abnormal bio-markers currently found. Keep it up!</p>
            )}
          </div>
        </div>

        {/* AI Health Recommendations Panel */}
        <div className="lg:col-span-7 bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between" id="ai-insights-card">
          <div>
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-teal-600" />
              AI Clinical Guidance
            </h3>
            
            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
              {riskScore && riskScore.recommendations.map((rec, idx) => {
                const isAlert = rec.includes('CRITICAL') || rec.includes('ALERT');
                return (
                  <div 
                    key={idx} 
                    className={`p-3.5 rounded-lg border flex gap-3 text-sm leading-relaxed ${
                      isAlert 
                        ? 'bg-red-50/70 border-red-100 text-red-900' 
                        : 'bg-teal-50/40 border-teal-50/80 text-gray-700'
                    }`}
                  >
                    {isAlert ? (
                      <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
                    )}
                    <p>{rec}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="border-t border-gray-100 pt-4 mt-6 flex justify-between items-center text-xs text-gray-500">
            <span>Powered by Gemini 3.6 & Arogya Clinical Engine</span>
            <button 
              onClick={() => onNavigate('report')}
              className="font-bold text-teal-600 hover:text-teal-700 text-sm flex items-center gap-1"
            >
              Prepare Doctor-Prep Report →
            </button>
          </div>
        </div>

      </div>

      {/* Grid: Upcoming Reminders & Recent Records */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Active Reminders Card */}
        <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between" id="active-reminders-card">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <Clock className="w-5 h-5 text-teal-600" />
                Medications & Schedules Due
              </h3>
              <button 
                onClick={() => onNavigate('reminders')}
                className="text-sm font-semibold text-teal-600 hover:text-teal-700"
              >
                Manage
              </button>
            </div>

            {reminders.length > 0 ? (
              <div className="space-y-3">
                {reminders.map((rem) => (
                  <div 
                    key={rem.reminder_id} 
                    className={`p-3 rounded-lg border flex items-center justify-between transition ${
                      rem.is_acknowledged 
                        ? 'bg-gray-50 border-gray-100 text-gray-400' 
                        : 'bg-white border-gray-200 text-gray-800 hover:border-teal-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <button 
                        onClick={() => handleAckReminder(rem.reminder_id, rem.is_acknowledged)}
                        className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors ${
                          rem.is_acknowledged 
                            ? 'bg-teal-600 border-teal-600 text-white' 
                            : 'border-gray-300 hover:border-teal-500 bg-white'
                        }`}
                        title={rem.is_acknowledged ? 'Mark as untaken' : 'Mark as taken'}
                      >
                        {rem.is_acknowledged && <span className="text-[10px] font-bold">✓</span>}
                      </button>
                      <div>
                        <p className={`text-sm font-medium ${rem.is_acknowledged ? 'line-through' : ''}`}>
                          {rem.title}
                        </p>
                        <p className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                          <Calendar className="w-3 h-3" />
                          Due: {new Date(rem.due_date).toLocaleDateString()}
                          {rem.recurrence !== 'NONE' && (
                            <span className="bg-teal-50 text-teal-700 px-1.5 py-0.2 rounded-full text-[10px] font-semibold uppercase ml-1.5">
                              {rem.recurrence}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>

                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      rem.reminder_type === 'MEDICATION' 
                        ? 'bg-teal-50 text-teal-700' 
                        : rem.reminder_type === 'DOCTOR_VISIT'
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'bg-yellow-50 text-yellow-700'
                    }`}>
                      {rem.reminder_type}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 border border-dashed border-gray-100 rounded-lg">
                <Calendar className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No upcoming active reminders.</p>
                <button 
                  onClick={() => onNavigate('reminders')}
                  className="text-xs text-teal-600 font-bold mt-1 hover:underline"
                >
                  Create manual reminder +
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Recent Health Records Card */}
        <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between" id="recent-records-card">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <FileText className="w-5 h-5 text-teal-600" />
                Recent Records & Reports
              </h3>
              <button 
                onClick={() => onNavigate('records')}
                className="text-sm font-semibold text-teal-600 hover:text-teal-700"
              >
                View Logs
              </button>
            </div>

            {records.length > 0 ? (
              <div className="space-y-3">
                {records.map((rec) => (
                  <div 
                    key={rec.record_id}
                    onClick={() => onSelectRecord(rec.record_id)}
                    className="p-3.5 rounded-lg border border-gray-100 hover:border-teal-200 hover:bg-teal-50/10 cursor-pointer transition flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-teal-50 flex items-center justify-center text-teal-700 font-bold">
                        {rec.record_type === 'LAB_REPORT' ? 'LR' : rec.record_type === 'PRESCRIPTION' ? 'PR' : 'DN'}
                      </div>
                      <div>
                        <p className="text-sm font-bold text-gray-800">
                          {rec.record_type.replace('_', ' ')}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          Report Date: {new Date(rec.report_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        rec.is_processed 
                          ? 'bg-green-50 text-green-700 border border-green-200' 
                          : 'bg-yellow-50 text-yellow-700 border border-yellow-200 animate-pulse'
                      }`}>
                        {rec.is_processed ? 'PROCESSED' : 'PROCESSING'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 border border-dashed border-gray-100 rounded-lg">
                <FileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No medical records uploaded yet.</p>
                <button 
                  onClick={() => onNavigate('upload')}
                  className="text-xs text-teal-600 font-bold mt-1 hover:underline"
                >
                  Upload your first lab test →
                </button>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
