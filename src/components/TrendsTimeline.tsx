import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ReferenceLine 
} from 'recharts';
import { 
  TrendingUp, 
  Activity, 
  Edit2, 
  Check, 
  X, 
  Info, 
  AlertTriangle,
  RefreshCw 
} from 'lucide-react';
import { api } from '../services/api.ts';
import { ClinicalParameter, ParameterStatus } from '../types.ts';

const SUPPORTED_PARAMETERS = [
  'HbA1c',
  'Fasting Blood Sugar',
  'Total Cholesterol',
  'LDL',
  'HDL',
  'Triglycerides',
  'Hemoglobin',
  'Creatinine',
  'eGFR',
  'Blood Pressure Systolic',
  'Blood Pressure Diastolic',
  'TSH',
  'Vitamin D',
  'Vitamin B12',
  'Uric Acid'
];

export const TrendsTimeline: React.FC = () => {
  const [availableParams, setAvailableParams] = useState<string[]>([]);
  const [selectedParam, setSelectedParam] = useState<string>('HbA1c');
  const [history, setHistory] = useState<ClinicalParameter[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingParamId, setEditingParamId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load list of all unique parameters currently having data
  const loadAvailableParameters = async () => {
    try {
      const allParams = await api.getParameters();
      // Extract unique names
      const uniqueNames = Array.from(new Set(allParams.map(p => p.param_name)));
      
      // Sort uniqueNames based on SUPPORTED_PARAMETERS order, put remaining at the end
      uniqueNames.sort((a, b) => {
        const idxA = SUPPORTED_PARAMETERS.indexOf(a);
        const idxB = SUPPORTED_PARAMETERS.indexOf(b);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return a.localeCompare(b);
      });

      setAvailableParams(uniqueNames);
      
      // Set active default to first available parameter or HbA1c
      if (uniqueNames.length > 0) {
        if (uniqueNames.includes('HbA1c')) {
          setSelectedParam('HbA1c');
        } else {
          setSelectedParam(uniqueNames[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load parameters:', err);
    }
  };

  const fetchParameterHistory = async (paramName: string) => {
    setLoading(true);
    try {
      const data = await api.getParameterHistory(paramName);
      // Sort ascending by date for chronological Recharts representation
      const sorted = [...data].sort((a, b) => new Date(a.report_date).getTime() - new Date(b.report_date).getTime());
      setHistory(sorted);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAvailableParameters();
  }, []);

  useEffect(() => {
    if (selectedParam) {
      fetchParameterHistory(selectedParam);
    }
  }, [selectedParam]);

  const startEdit = (param: ClinicalParameter) => {
    setEditingParamId(param.param_id);
    setEditValue(param.value.toString());
  };

  const cancelEdit = () => {
    setEditingParamId(null);
    setEditValue('');
  };

  const saveEdit = async (paramId: string) => {
    const numVal = parseFloat(editValue);
    if (isNaN(numVal) || numVal <= 0) {
      alert('Please enter a valid positive number');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.updateParameter(paramId, numVal);
      // Re-fetch history & re-compute overall risk score in backend
      await Promise.all([
        fetchParameterHistory(selectedParam),
        api.recomputeRiskScore()
      ]);
      setEditingParamId(null);
    } catch (err: any) {
      alert('Failed to update parameter: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Prepare chart dataset
  const chartData = history.map(item => ({
    date: new Date(item.report_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' }),
    value: item.value,
    status: item.status,
    rawDate: item.report_date
  }));

  // Find reference range defaults from current item
  const sampleItem = history[0];
  const minRef = sampleItem?.reference_range_min;
  const maxRef = sampleItem?.reference_range_max;
  const unit = sampleItem?.unit || '';

  // Get status class for table display
  const getStatusBadgeClass = (status: ParameterStatus) => {
    switch (status) {
      case 'NORMAL':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'LOW':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'CRITICAL':
        return 'bg-red-50 text-red-700 border-red-200 animate-pulse';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="space-y-8" id="trends-timeline-view">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-teal-600" />
            Bio-Marker Trend Analytics
          </h2>
          <p className="text-sm text-gray-500 mt-1"> Chronological timeline charts of your clinical lab records.</p>
        </div>

        {/* Param Dropdown Selector */}
        {availableParams.length > 0 ? (
          <div className="flex items-center gap-2 w-full md:w-auto">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider whitespace-nowrap">Analyze bio-marker:</span>
            <select
              value={selectedParam}
              onChange={(e) => setSelectedParam(e.target.value)}
              className="px-3.5 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-semibold focus:outline-none focus:ring-2 focus:ring-teal-500 w-full md:w-56"
              id="select-trend-parameter"
            >
              {availableParams.map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </div>
        ) : (
          <span className="text-sm text-gray-400 italic">No historical data available.</span>
        )}
      </div>

      {availableParams.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Main Line Chart */}
          <div className="lg:col-span-8 bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between" id="trend-chart-panel">
            <div>
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-teal-600" />
                  Chronological Trend — {selectedParam}
                </h3>
                {minRef !== null && maxRef !== null && (
                  <span className="text-xs font-semibold text-gray-500 bg-gray-50 border border-gray-100 px-2.5 py-1 rounded-md">
                    Normal Reference Range: <strong className="text-teal-700">{minRef} - {maxRef} {unit}</strong>
                  </span>
                )}
              </div>

              {loading ? (
                <div className="h-72 flex items-center justify-center">
                  <RefreshCw className="w-8 h-8 text-teal-600 animate-spin" />
                </div>
              ) : history.length > 0 ? (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                      <XAxis 
                        dataKey="date" 
                        stroke="#9ca3af" 
                        fontSize={11} 
                        tickLine={false} 
                        axisLine={false}
                      />
                      <YAxis 
                        stroke="#9ca3af" 
                        fontSize={11} 
                        tickLine={false} 
                        axisLine={false}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip 
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload;
                            return (
                              <div className="bg-white border border-gray-100 rounded-lg p-3 shadow-lg text-xs space-y-1">
                                <p className="font-bold text-gray-800">{data.date}</p>
                                <p className="text-teal-700 font-semibold">Value: {data.value} {unit}</p>
                                <p className="text-gray-500 flex items-center gap-1">
                                  Status: 
                                  <span className="font-bold">{data.status}</span>
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      {/* Horizontal lines indicating references if available */}
                      {minRef !== null && minRef !== undefined && (
                        <ReferenceLine y={minRef} stroke="#93c5fd" strokeDasharray="4 4" label={{ value: 'Min Normal', fill: '#3b82f6', fontSize: 10, position: 'insideBottomLeft' }} />
                      )}
                      {maxRef !== null && maxRef !== undefined && (
                        <ReferenceLine y={maxRef} stroke="#fdba74" strokeDasharray="4 4" label={{ value: 'Max Normal', fill: '#f97316', fontSize: 10, position: 'insideTopLeft' }} />
                      )}
                      <Line 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#0D9488" 
                        strokeWidth={3} 
                        dot={{ r: 6, fill: '#0D9488', strokeWidth: 0 }}
                        activeDot={{ r: 8, strokeWidth: 0 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-72 flex flex-col items-center justify-center text-center text-gray-500 italic">
                  No readings found.
                </div>
              )}
            </div>
            
            <p className="text-[11px] text-gray-400 leading-relaxed mt-4 flex items-center gap-1.5 bg-gray-50 p-2.5 rounded-lg border border-gray-100">
              <Info className="w-4 h-4 text-gray-500 shrink-0" />
              <span>Reference ranges are dynamically pulled from standard clinical guidelines. Always consult with a qualified medical professional for diagnosis interpretation.</span>
            </p>
          </div>

          {/* Historical Readings Table with Correction Action */}
          <div className="lg:col-span-4 bg-white border border-gray-100 rounded-xl p-6 shadow-sm" id="trend-readings-table">
            <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wider mb-4">Readings History</h3>
            
            <div className="space-y-4 max-h-[380px] overflow-y-auto pr-1">
              {history.map((reading) => {
                const isEditing = editingParamId === reading.param_id;
                return (
                  <div key={reading.param_id} className="p-3 border border-gray-100 rounded-xl bg-white space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-gray-500">
                        {new Date(reading.report_date).toLocaleDateString()}
                      </span>
                      
                      {!isEditing ? (
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getStatusBadgeClass(reading.status)}`}>
                          {reading.status}
                        </span>
                      ) : (
                        <span className="text-[10px] text-teal-600 font-bold animate-pulse">CORRECTING</span>
                      )}
                    </div>

                    <div className="flex items-center justify-between">
                      {isEditing ? (
                        <div className="flex items-center gap-1.5 w-full mt-1">
                          <input
                            type="number"
                            step="any"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-sm text-gray-800 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 w-24"
                            disabled={isSubmitting}
                            id={`input-edit-param-${reading.param_id}`}
                          />
                          <span className="text-xs text-gray-500 mr-2">{unit}</span>
                          <button
                            onClick={() => saveEdit(reading.param_id)}
                            disabled={isSubmitting}
                            className="p-1 bg-green-50 text-green-700 border border-green-200 rounded hover:bg-green-100 transition"
                            title="Save"
                            id={`btn-save-param-${reading.param_id}`}
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={cancelEdit}
                            disabled={isSubmitting}
                            className="p-1 bg-red-50 text-red-700 border border-red-200 rounded hover:bg-red-100 transition"
                            title="Cancel"
                            id={`btn-cancel-param-${reading.param_id}`}
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <>
                          <span className="text-lg font-bold text-gray-800">
                            {reading.value} <span className="text-xs text-gray-500 font-normal">{unit}</span>
                          </span>
                          <button
                            onClick={() => startEdit(reading)}
                            className="p-1.5 text-gray-400 hover:text-teal-600 border border-gray-100 rounded hover:bg-gray-50 transition"
                            title="Correct OCR value"
                            id={`btn-edit-param-${reading.param_id}`}
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      ) : (
        <div className="bg-white border border-gray-100 rounded-xl p-12 text-center shadow-sm">
          <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3 animate-pulse" />
          <h3 className="text-lg font-bold text-gray-800">No Historical Bio-markers</h3>
          <p className="text-sm text-gray-500 mt-1 max-w-sm mx-auto">
            Once you upload a lab blood report or write manual notes containing parameters, their historical timelines will draw automatically.
          </p>
        </div>
      )}
    </div>
  );
};
