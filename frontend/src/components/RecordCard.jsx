import React from 'react';
import { FileText, Download, Trash2, CheckCircle2, Clock, Eye } from 'lucide-react';
import { formatDate } from '../utils/formatDate';

export default function RecordCard({ record, onDownload, onDelete, onViewDetails }) {
  const getRecordTypeBadge = (type) => {
    switch (type) {
      case 'LAB_REPORT':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'PRESCRIPTION':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'DOCTOR_NOTE':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'MANUAL_ENTRY':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="glass-card rounded-2xl p-5 border border-gray-200 hover:border-accent/40 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${getRecordTypeBadge(record.record_type)}`}>
                {record.record_type.replace('_', ' ')}
              </span>
              <p className="text-xs text-gray-500 mt-1">
                Report Date: <span className="font-medium text-gray-700">{formatDate(record.report_date)}</span>
              </p>
            </div>
          </div>

          <div>
            {record.is_processed ? (
              <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200" title="Processed by AI pipeline">
                <CheckCircle2 className="w-3 h-3" /> Processed
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 animate-pulse">
                <Clock className="w-3 h-3" /> Processing
              </span>
            )}
          </div>
        </div>

        {/* Extracted entities summary */}
        {record.extracted_entities?.parameters && record.extracted_entities.parameters.length > 0 && (
          <div className="mt-3.5 pt-3 border-t border-gray-100">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1.5">
              Extracted Parameters
            </span>
            <div className="flex flex-wrap gap-1.5">
              {record.extracted_entities.parameters.slice(0, 4).map((p, idx) => (
                <span
                  key={idx}
                  className="text-xs font-mono bg-gray-50 text-gray-700 px-2 py-0.5 rounded border border-gray-200"
                >
                  {p.name}: <strong className="text-gray-900">{p.value}</strong> {p.unit}
                </span>
              ))}
              {record.extracted_entities.parameters.length > 4 && (
                <span className="text-[10px] text-gray-400 self-center">
                  +{record.extracted_entities.parameters.length - 4} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
        <span className="text-[11px] text-gray-400">
          Uploaded {formatDate(record.upload_date)}
        </span>

        <div className="flex items-center gap-1.5">
          {onViewDetails && (
            <button
              onClick={() => onViewDetails(record.record_id)}
              className="p-1.5 text-gray-500 hover:text-primary hover:bg-gray-100 rounded-lg transition-colors"
              title="View record details"
            >
              <Eye className="w-4 h-4" />
            </button>
          )}

          {record.source_file_path && onDownload && (
            <button
              onClick={() => onDownload(record.record_id)}
              className="p-1.5 text-gray-500 hover:text-primary hover:bg-gray-100 rounded-lg transition-colors"
              title="Download decrypted document"
            >
              <Download className="w-4 h-4" />
            </button>
          )}

          {onDelete && (
            <button
              onClick={() => onDelete(record.record_id)}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete record"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
