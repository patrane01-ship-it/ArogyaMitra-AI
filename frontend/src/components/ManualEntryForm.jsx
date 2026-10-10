import React, { useState } from 'react';
import { Plus, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';
import { SUPPORTED_PARAMETERS } from '../utils/parameterConfig';
import { createManualRecord } from '../services/api';

export default function ManualEntryForm({ onSuccess }) {
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [parameters, setParameters] = useState([
    {
      param_name: 'HbA1c',
      value: '',
      unit: '%',
      reference_range_min: 4.0,
      reference_range_max: 5.7,
    },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleParamSelect = (index, name) => {
    const config = SUPPORTED_PARAMETERS.find((p) => p.name === name);
    const updated = [...parameters];
    updated[index] = {
      ...updated[index],
      param_name: name,
      unit: config?.unit || '',
      reference_range_min: config?.ref_min ?? null,
      reference_range_max: config?.ref_max ?? null,
    };
    setParameters(updated);
  };

  const handleValueChange = (index, value) => {
    const updated = [...parameters];
    updated[index].value = value;
    setParameters(updated);
  };

  const addRow = () => {
    const defaultParam = SUPPORTED_PARAMETERS[0];
    setParameters([
      ...parameters,
      {
        param_name: defaultParam.name,
        value: '',
        unit: defaultParam.unit,
        reference_range_min: defaultParam.ref_min,
        reference_range_max: defaultParam.ref_max,
      },
    ]);
  };

  const removeRow = (index) => {
    if (parameters.length === 1) return;
    setParameters(parameters.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Validate
    const validParams = parameters.filter((p) => p.value && !isNaN(parseFloat(p.value)));
    if (validParams.length === 0) {
      setError('Please provide a valid test reading for at least one parameter');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        record_type: 'MANUAL_ENTRY',
        report_date: new Date(reportDate).toISOString(),
        notes,
        parameters: validParams.map((p) => ({
          param_name: p.param_name,
          value: parseFloat(p.value),
          unit: p.unit,
          reference_range_min: p.reference_range_min,
          reference_range_max: p.reference_range_max,
        })),
      };

      const res = await createManualRecord(payload);
      setSuccess('Manual readings recorded and added to health timeline!');
      setParameters([
        {
          param_name: 'HbA1c',
          value: '',
          unit: '%',
          reference_range_min: 4.0,
          reference_range_max: 5.7,
        },
      ]);
      setNotes('');
      if (onSuccess) onSuccess(res);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save readings');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 border border-gray-200">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Test Reading Date
            </label>
            <input
              type="date"
              value={reportDate}
              max={new Date().toISOString().split('T')[0]}
              onChange={(e) => setReportDate(e.target.value)}
              className="w-full text-xs rounded-xl border border-gray-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Lab or Physician Notes (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Fasting 12 hrs, LabCorp"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full text-xs rounded-xl border border-gray-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        </div>

        {/* Dynamic Parameter Rows */}
        <div className="space-y-3 pt-2">
          <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
            Clinical Parameters
          </label>

          {parameters.map((p, index) => (
            <div
              key={index}
              className="flex flex-col sm:flex-row items-center gap-2 p-3 rounded-xl bg-gray-50 border border-gray-200"
            >
              <select
                value={p.param_name}
                onChange={(e) => handleParamSelect(index, e.target.value)}
                className="w-full sm:w-1/2 text-xs rounded-lg border border-gray-300 p-2 bg-white"
              >
                {SUPPORTED_PARAMETERS.map((sp) => (
                  <option key={sp.name} value={sp.name}>
                    {sp.name} ({sp.unit})
                  </option>
                ))}
              </select>

              <div className="flex items-center gap-2 w-full sm:w-1/2">
                <input
                  type="number"
                  step="any"
                  placeholder="Value"
                  value={p.value}
                  onChange={(e) => handleValueChange(index, e.target.value)}
                  className="w-full text-xs rounded-lg border border-gray-300 p-2 bg-white font-mono"
                  required
                />
                <span className="text-xs font-mono text-gray-500 w-16 text-center">
                  {p.unit}
                </span>

                <button
                  type="button"
                  onClick={() => removeRow(index)}
                  disabled={parameters.length === 1}
                  className="p-1.5 text-gray-400 hover:text-red-500 disabled:opacity-30"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          <button
            type="button"
            onClick={addRow}
            className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary-dark mt-2"
          >
            <Plus className="w-4 h-4" /> Add Another Clinical Test
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{success}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 px-4 rounded-xl bg-accent-dark hover:bg-primary text-white font-medium text-sm transition-all shadow-md shadow-accent/20"
        >
          {submitting ? 'Saving...' : 'Save Manual Record'}
        </button>
      </form>
    </div>
  );
}
