import React, { useState, useEffect } from 'react';
import { ArrowLeft, Download, FileText, CheckCircle2, Clock, Shield } from 'lucide-react';
import { getRecordById, downloadRecord } from '../services/api';
import { formatDate, formatDateTime } from '../utils/formatDate';

export default function RecordDetailPage({ recordId, setActivePage }) {
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRecord = async () => {
      setLoading(true);
      try {
        const data = await getRecordById(recordId);
        setRecord(data);
      } catch (err) {
        setError('Record not found or access denied.');
      } finally {
        setLoading(false);
      }
    };

    if (recordId) {
      fetchRecord();
    }
  }, [recordId]);

  const handleDownload = async () => {
    try {
      const blob = await downloadRecord(recordId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `record_${recordId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch {
      alert('Download failed.');
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-gray-500">
        Loading document details...
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-sm text-red-600 font-semibold">{error || 'Record unavailable'}</p>
        <button
          onClick={() => setActivePage('dashboard')}
          className="mt-4 px-4 py-2 bg-primary text-white text-xs rounded-xl"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setActivePage('dashboard')}
          className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-primary font-medium transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
        </button>

        {record.source_file_path && (
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-white text-xs font-semibold hover:bg-primary-dark transition-all"
          >
            <Download className="w-3.5 h-3.5" /> Download Decrypted File
          </button>
        )}
      </div>

      {/* Overview Card */}
      <div className="glass-card rounded-2xl p-6 border border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100">
          <div>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
              {record.record_type.replace('_', ' ')}
            </span>
            <h1 className="text-xl font-bold text-gray-900 mt-2">
              Medical Document #{record.record_id.slice(0, 8)}
            </h1>
          </div>

          <div>
            {record.is_processed ? (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" /> AI Ingestion Complete
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 bg-amber-50 px-3 py-1 rounded-full border border-amber-200 animate-pulse">
                <Clock className="w-3.5 h-3.5" /> Pipeline Running
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4 text-xs">
          <div>
            <span className="text-gray-400 block font-medium">Document Date</span>
            <span className="font-semibold text-gray-800">{formatDate(record.report_date)}</span>
          </div>
          <div>
            <span className="text-gray-400 block font-medium">Ingestion Timestamp</span>
            <span className="font-semibold text-gray-800">{formatDateTime(record.upload_date)}</span>
          </div>
          <div>
            <span className="text-gray-400 block font-medium">At-Rest Encryption</span>
            <span className="font-semibold text-emerald-700 flex items-center gap-1">
              <Shield className="w-3.5 h-3.5" /> AES-256-GCM Active
            </span>
          </div>
        </div>
      </div>

      {/* Extracted Parameters */}
      <div className="glass-card rounded-2xl p-6 border border-gray-200">
        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">
          Extracted Clinical Parameters
        </h3>

        {record.extracted_entities?.parameters && record.extracted_entities.parameters.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500">
                  <th className="pb-3 font-semibold">Parameter</th>
                  <th className="pb-3 font-semibold">Value</th>
                  <th className="pb-3 font-semibold">Unit</th>
                  <th className="pb-3 font-semibold">Reference Range</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {record.extracted_entities.parameters.map((p, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/70">
                    <td className="py-2.5 font-medium text-gray-800">{p.name}</td>
                    <td className="py-2.5 font-mono font-bold text-primary">{p.value}</td>
                    <td className="py-2.5 font-mono text-gray-500">{p.unit}</td>
                    <td className="py-2.5 font-mono text-gray-500">
                      {p.ref_min ?? 'N/A'} - {p.ref_max ?? 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-gray-500">
            No discrete numerical parameters were detected in this document.
          </p>
        )}
      </div>

      {/* Raw OCR Text Preview */}
      {record.raw_text && (
        <div className="glass-card rounded-2xl p-6 border border-gray-200">
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-3">
            OCR Extracted Text Preview
          </h3>
          <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 font-mono text-xs text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto">
            {record.raw_text}
          </div>
        </div>
      )}
    </div>
  );
}
