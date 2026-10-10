import React, { useState, useEffect } from 'react';
import { TrendingUp, Filter, AlertCircle, Edit2, Check, X } from 'lucide-react';
import HealthTimeline from '../components/HealthTimeline';
import { SUPPORTED_PARAMETERS } from '../utils/parameterConfig';
import { getParamHistory, updateParam } from '../services/api';
import { formatDate } from '../utils/formatDate';
import { getStatusBadge } from '../utils/riskColors';

export default function TimelinePage() {
  const [selectedParam, setSelectedParam] = useState('HbA1c');
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Edit state
  const [editingParamId, setEditingParamId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [editUnit, setEditUnit] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const fetchHistory = async (paramName) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getParamHistory(paramName);
      setHistoryData(data);
    } catch (err) {
      setHistoryData(null);
      setError(`No recorded readings found for "${paramName}". Ingest reports to populate this parameter.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(selectedParam);
  }, [selectedParam]);

  const handleStartEdit = (reading) => {
    setEditingParamId(reading.param_id || 'reading');
    setEditValue(reading.value);
    setEditUnit(historyData?.unit || '');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header & Parameter Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-primary" /> Health Trajectory & Trends
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Track multi-year biometric trajectories against clinical reference baselines
          </p>
        </div>

        {/* Dropdown Selector */}
        <div className="flex items-center gap-2 bg-white p-1.5 rounded-xl border border-gray-200 shadow-xs">
          <Filter className="w-4 h-4 text-gray-400 ml-2" />
          <select
            value={selectedParam}
            onChange={(e) => setSelectedParam(e.target.value)}
            className="text-xs font-semibold text-gray-800 bg-transparent pr-4 py-1.5 focus:outline-none"
          >
            {SUPPORTED_PARAMETERS.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name} ({p.unit})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Chart Section */}
      {loading ? (
        <div className="glass-card rounded-2xl p-12 text-center border border-gray-200 flex flex-col items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-xs text-gray-500 font-medium">Loading historical trend points...</p>
        </div>
      ) : error ? (
        <div className="glass-card rounded-2xl p-8 text-center border border-gray-200/80 bg-gray-50/50">
          <AlertCircle className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm font-semibold text-gray-700">{error}</p>
          <p className="text-xs text-gray-500 mt-1">
            Select another parameter or upload your lab tests from the Upload page.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <HealthTimeline historyData={historyData} />

          {/* Historical Readings Table */}
          <div className="glass-card rounded-2xl p-6 border border-gray-200">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">
              Historical Readings Log ({selectedParam})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-gray-200 text-gray-500">
                    <th className="pb-3 font-semibold">Test Date</th>
                    <th className="pb-3 font-semibold">Measured Value</th>
                    <th className="pb-3 font-semibold">Reference Range</th>
                    <th className="pb-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {historyData?.readings?.map((r, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/70 transition-colors">
                      <td className="py-3 font-medium text-gray-800">
                        {formatDate(r.report_date)}
                      </td>
                      <td className="py-3 font-mono font-bold text-primary">
                        {r.value} {historyData.unit}
                      </td>
                      <td className="py-3 font-mono text-gray-500">
                        {historyData.reference_range_min ?? 'N/A'} - {historyData.reference_range_max ?? 'N/A'} {historyData.unit}
                      </td>
                      <td className="py-3">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getStatusBadge(r.status)}`}>
                          {r.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
