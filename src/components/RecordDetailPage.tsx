import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  ArrowLeft, 
  FileText, 
  Trash2, 
  CheckCircle, 
  AlertTriangle, 
  Activity, 
  Clock, 
  ShieldCheck, 
  ChevronDown, 
  ChevronUp, 
  Edit2, 
  Check, 
  X 
} from 'lucide-react';
import { api } from '../services/api.ts';
import { HealthRecord, ClinicalParameter, ParameterStatus } from '../types.ts';

interface RecordDetailPageProps {
  recordId: string;
  onBack: () => void;
}

export const RecordDetailPage: React.FC<RecordDetailPageProps> = ({ recordId, onBack }) => {
  const [record, setRecord] = useState<HealthRecord | null>(null);
  const [params, setParams] = useState<ClinicalParameter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRawText, setShowRawText] = useState(false);

  // Edit fields state
  const [editingParamId, setEditingParamId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [submittingEdit, setSubmittingEdit] = useState(false);

  const fetchRecordDetails = async () => {
    try {
      setLoading(true);
      const data = await api.getRecord(recordId);
      setRecord(data);
      
      // Get all parameters, filter by this record_id
      const allParams = await api.getParameters();
      const filtered = allParams.filter(p => p.record_id === recordId);
      setParams(filtered);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load record details:', err);
      setError(err.message || 'Failed to load details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordDetails();
  }, [recordId]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this record? This removes all its clinical trends.')) return;
    try {
      await api.deleteRecord(recordId);
      await api.recomputeRiskScore();
      onBack();
    } catch (err: any) {
      alert('Delete failed: ' + err.message);
    }
  };

  const startEdit = (param: ClinicalParameter) => {
    setEditingParamId(param.param_id);
    setEditValue(param.value.toString());
  };

  const cancelEdit = () => {
    setEditingParamId(null);
    setEditValue('');
  };

  const saveEdit = async (paramId: string) => {
    const num = parseFloat(editValue);
    if (isNaN(num) || num <= 0) {
      alert('Please enter a valid positive number');
      return;
    }

    setSubmittingEdit(true);
    try {
      await api.updateParameter(paramId, num);
      // Re-fetch parameters and recompute risk
      await Promise.all([
        fetchRecordDetails(),
        api.recomputeRiskScore()
      ]);
      setEditingParamId(null);
    } catch (err: any) {
      alert('Failed to update: ' + err.message);
    } finally {
      setSubmittingEdit(false);
    }
  };

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

  if (loading) {
    return (
      <div className="bg-white border border-gray-100 rounded-xl p-20 flex flex-col justify-center items-center">
        <Clock className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-500 font-medium font-serif text-lg">Decrypting encrypted healthcare records...</p>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 p-6 rounded-xl flex flex-col items-center text-center max-w-lg mx-auto my-12" id="detail-error">
        <AlertTriangle className="w-12 h-12 text-red-600 mb-3" />
        <h3 className="text-lg font-bold mb-1">Details Unavailable</h3>
        <p className="text-sm text-red-700 mb-4">{error || 'Record details not found.'}</p>
        <button 
          onClick={onBack}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition"
        >
          Return to Logs
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6" id="record-detail-view">
      
      {/* Navigation Header */}
      <div className="flex justify-between items-center bg-white p-4 border border-gray-100 rounded-xl shadow-sm">
        <button
          onClick={onBack}
          className="px-4 py-2 hover:bg-gray-50 text-gray-700 font-semibold rounded-lg flex items-center gap-2 transition text-sm border border-gray-100"
          id="btn-back-to-logs"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Index
        </button>

        <button
          onClick={handleDelete}
          className="px-4 py-2 hover:bg-red-50 text-red-700 font-semibold rounded-lg flex items-center gap-2 transition text-sm border border-red-100"
          id="btn-delete-record"
        >
          <Trash2 className="w-4 h-4" />
          Delete Document
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Main Parameters list */}
        <div className="lg:col-span-8 bg-white border border-gray-100 rounded-xl p-6 shadow-sm space-y-6" id="detail-parameters-panel">
          <div>
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <Activity className="w-5 h-5 text-teal-600" />
              Extracted Clinical Bio-markers
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Parsed from document dated {new Date(record.report_date).toLocaleDateString()}. Double check and correct values as needed.
            </p>
          </div>

          {params.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {params.map((p) => {
                const isEditing = editingParamId === p.param_id;
                return (
                  <div key={p.param_id} className="p-4 border border-gray-100 bg-white rounded-xl space-y-3 shadow-sm hover:border-teal-100 transition">
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-gray-700 text-sm">{p.param_name}</span>
                      {!isEditing && (
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getStatusBadgeClass(p.status)}`}>
                          {p.status}
                        </span>
                      )}
                    </div>

                    <div className="flex justify-between items-end">
                      {isEditing ? (
                        <div className="flex items-center gap-1.5 w-full">
                          <input
                            type="number"
                            step="any"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-sm font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 w-24"
                            disabled={submittingEdit}
                            id={`input-edit-detail-${p.param_id}`}
                          />
                          <span className="text-xs text-gray-500 mr-2">{p.unit}</span>
                          <button
                            onClick={() => saveEdit(p.param_id)}
                            disabled={submittingEdit}
                            className="p-1 bg-green-50 text-green-700 border border-green-200 rounded hover:bg-green-100 transition"
                            id={`btn-save-detail-${p.param_id}`}
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={cancelEdit}
                            disabled={submittingEdit}
                            className="p-1 bg-red-50 text-red-700 border border-red-200 rounded hover:bg-red-100 transition"
                            id={`btn-cancel-detail-${p.param_id}`}
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <>
                          <div>
                            <p className="text-2xl font-bold text-gray-900 leading-none">
                              {p.value} <span className="text-xs font-normal text-gray-500">{p.unit}</span>
                            </p>
                            {p.reference_range_min !== null && p.reference_range_max !== null && (
                              <p className="text-[10px] text-gray-400 font-semibold mt-1.5">
                                Normal Range: {p.reference_range_min} - {p.reference_range_max}
                              </p>
                            )}
                          </div>
                          
                          <button
                            onClick={() => startEdit(p)}
                            className="p-1.5 text-gray-450 hover:text-teal-600 border border-gray-100 rounded hover:bg-gray-50 transition"
                            title="Correct OCR error"
                            id={`btn-edit-detail-${p.param_id}`}
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
          ) : (
            <div className="p-8 text-center bg-gray-50 border border-dashed rounded-xl text-gray-500">
              <AlertTriangle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
              <p className="text-sm font-semibold">No bio-markers parsed from this document.</p>
              <p className="text-xs text-gray-400 mt-1">If this was a lab report, check if the parameters were structured properly.</p>
            </div>
          )}

          {/* Raw Text Collapsible Panel */}
          {record.raw_text && (
            <div className="border-t border-gray-100 pt-6 mt-6">
              <button
                onClick={() => setShowRawText(!showRawText)}
                className="w-full flex justify-between items-center py-2 text-sm font-bold text-gray-600 hover:text-teal-600 transition"
                id="btn-toggle-raw-text"
              >
                <span>Raw Transcript Decrypted (OCR Text)</span>
                {showRawText ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              <AnimatePresence>
                {showRawText && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden mt-2"
                  >
                    <pre className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-600 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                      {record.raw_text}
                    </pre>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Right Info Panel */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm space-y-4" id="record-security-card">
            <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-4.5 h-4.5 text-teal-600" />
              Security Integrity
            </h3>

            <div className="text-xs space-y-3.5 text-gray-600 leading-relaxed">
              <p>
                This health record is protected under <strong>AES-256-GCM symmetric encryption</strong>. Standard healthcare privacy protocols are maintained across our server nodes.
              </p>
              
              <div className="p-3 bg-gray-50 border rounded-lg space-y-1 font-mono text-[10px]">
                <p className="font-bold text-gray-500">Document Hash (SHA-256):</p>
                <p className="text-gray-600 break-all">{record.encryption_hash || 'SHA-256-UNAVAILABLE'}</p>
              </div>

              <div className="p-3 bg-teal-50/40 border border-teal-100 rounded-lg space-y-1 text-teal-800">
                <p className="font-bold">Processed Status:</p>
                <p className="font-semibold text-[11px] uppercase">{record.is_processed ? 'STANDARDIZED & CLINICALLY EVALUATED' : 'PROCESSING'}</p>
              </div>

              {record.source_file_path && (
                <div className="pt-2">
                  <a
                    href={`/api/records/${record.record_id}/download`}
                    download
                    className="w-full flex justify-center items-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg shadow-sm transition-colors text-center"
                    id="btn-download-decrypted-file"
                  >
                    <FileText className="w-4 h-4" />
                    Decrypt & Download Document
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
