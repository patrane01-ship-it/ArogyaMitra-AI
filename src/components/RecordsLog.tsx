import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  FileText, 
  Trash2, 
  Calendar, 
  Search, 
  Filter, 
  CheckCircle, 
  AlertTriangle, 
  Maximize2, 
  Eye, 
  Clock,
  Download
} from 'lucide-react';
import { api } from '../services/api.ts';
import { HealthRecord, RecordType } from '../types.ts';

interface RecordsLogProps {
  onSelectRecord: (recordId: string) => void;
  searchTerm: string;
  setSearchTerm: (val: string) => void;
}

export const RecordsLog: React.FC<RecordsLogProps> = ({ onSelectRecord, searchTerm, setSearchTerm }) => {
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false);

  const exportAsCSV = (data: any[], filename: string) => {
    if (data.length === 0) {
      alert("No data available to export.");
      return;
    }
    const headers = Object.keys(data[0]);
    const csvRows = [
      headers.join(','), // header row
      ...data.map(row => 
        headers.map(fieldName => {
          const value = row[fieldName];
          const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value || '');
          // Escape quotes
          const escaped = stringValue.replace(/"/g, '""');
          return `"${escaped}"`;
        }).join(',')
      )
    ];

    const csvContent = "data:text/csv;charset=utf-8," + csvRows.join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportAsJSON = (data: any, filename: string) => {
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
      JSON.stringify(data, null, 2)
    )}`;
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', jsonString);
    downloadAnchor.setAttribute('download', filename);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.removeChild(downloadAnchor);
  };

  const handleExportJSON = async () => {
    try {
      const recordsData = await api.getRecords();
      const parametersData = await api.getParameters();
      const exportData = {
        exported_at: new Date().toISOString(),
        medical_records: recordsData,
        clinical_parameters: parametersData
      };
      exportAsJSON(exportData, 'arogyamitra_clinical_data_export.json');
    } catch (err) {
      console.error('Export failed:', err);
      alert('Export failed: Unable to fetch full clinical data.');
    }
  };

  const handleExportRecordsCSV = async () => {
    try {
      const recordsData = await api.getRecords();
      const flattened = recordsData.map(r => ({
        record_id: r.record_id,
        record_type: r.record_type,
        report_date: new Date(r.report_date).toLocaleDateString(),
        is_processed: r.is_processed ? 'Yes' : 'No',
        extracted_entities_count: r.extracted_entities ? Object.keys(r.extracted_entities).length : 0,
        raw_text_preview: r.raw_text ? r.raw_text.substring(0, 100).replace(/\n/g, ' ') : ''
      }));
      exportAsCSV(flattened, 'arogyamitra_medical_records.csv');
    } catch (err) {
      console.error('Export failed:', err);
      alert('Export failed: Unable to fetch records.');
    }
  };

  const handleExportParametersCSV = async () => {
    try {
      const parametersData = await api.getParameters();
      const flattened = parametersData.map(p => ({
        parameter_id: p.param_id,
        parameter_name: p.param_name,
        value: p.value,
        unit: p.unit,
        status: p.status,
        report_date: new Date(p.report_date).toLocaleDateString(),
        record_id: p.record_id
      }));
      exportAsCSV(flattened, 'arogyamitra_clinical_parameters.csv');
    } catch (err) {
      console.error('Export failed:', err);
      alert('Export failed: Unable to fetch clinical parameters.');
    }
  };

  const fetchRecords = async () => {
    try {
      const data = await api.getRecords();
      setRecords(data);
    } catch (err) {
      console.error('Failed to fetch records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Warning: Deleting this clinical record will remove all its extracted parameters, modify your timeline trends, and affect your risk evaluation. Do you want to proceed?')) {
      return;
    }

    try {
      await api.deleteRecord(id);
      // Re-fetch records and trigger risk recomputation
      setRecords(prev => prev.filter(r => r.record_id !== id));
      await api.recomputeRiskScore();
    } catch (err: any) {
      alert('Delete failed: ' + err.message);
    }
  };

  const filteredRecords = records.filter(r => {
    const title = r.record_type.replace('_', ' ').toLowerCase();
    const formattedDate = new Date(r.report_date).toLocaleDateString().toLowerCase();
    const rawDateStr = r.report_date.toLowerCase();
    const query = searchTerm.toLowerCase();

    const matchesSearch = title.includes(query) || 
                          formattedDate.includes(query) ||
                          rawDateStr.includes(query) ||
                          (r.raw_text && r.raw_text.toLowerCase().includes(query)) ||
                          (r.source_file_path && r.source_file_path.toLowerCase().includes(query));
    
    const matchesType = selectedType === 'ALL' || r.record_type === selectedType;

    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6" id="records-log-view">
      
      {/* Header controls */}
      <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <FileText className="w-5 h-5 text-teal-600" />
            Medical Records Index
          </h2>
          <p className="text-sm text-gray-500 mt-1">Audit, inspect, or manage processed documents and raw OCR transcripts.</p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto items-stretch sm:items-center">
          {/* Search Box */}
          <div className="relative flex-1 sm:w-60">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search reports by title or date..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-teal-500 text-gray-800"
              id="input-record-search"
            />
          </div>

          {/* Record Type select */}
          <div className="relative">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full pl-3 pr-8 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-teal-500 appearance-none cursor-pointer"
              id="select-record-filter"
            >
              <option value="ALL">All Document Classes</option>
              <option value="LAB_REPORT">Lab Blood Reports</option>
              <option value="PRESCRIPTION">Prescriptions</option>
              <option value="DOCTOR_NOTE">Physician Notes</option>
              <option value="IMAGING">Imaging Reports</option>
              <option value="MANUAL_ENTRY">Manual Entry Logs</option>
            </select>
            <Filter className="absolute right-3 top-2.5 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
          </div>

          {/* Export Dropdown */}
          <div className="relative">
            <button
              onClick={() => setExportDropdownOpen(!exportDropdownOpen)}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition-colors shadow-sm cursor-pointer whitespace-nowrap"
              id="btn-export-dropdown-toggle"
            >
              <Download className="w-3.5 h-3.5" />
              Export Data
            </button>

            {exportDropdownOpen && (
              <>
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setExportDropdownOpen(false)} 
                />
                <div 
                  className="absolute right-0 mt-2 w-56 bg-white border border-gray-150 rounded-xl shadow-lg py-2 z-20"
                  id="export-dropdown-menu"
                >
                  <div className="px-3 py-1.5 border-b border-gray-100 mb-1">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Select Export Format</p>
                  </div>
                  <button
                    onClick={() => {
                      handleExportJSON();
                      setExportDropdownOpen(false);
                    }}
                    className="w-full text-left px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-teal-50 hover:text-teal-800 flex items-center gap-2 transition"
                    id="btn-export-json"
                  >
                    <FileText className="w-3.5 h-3.5 text-teal-600" />
                    Complete clinical data (JSON)
                  </button>
                  <button
                    onClick={() => {
                      handleExportRecordsCSV();
                      setExportDropdownOpen(false);
                    }}
                    className="w-full text-left px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-teal-50 hover:text-teal-800 flex items-center gap-2 transition"
                    id="btn-export-records-csv"
                  >
                    <FileText className="w-3.5 h-3.5 text-teal-600" />
                    Medical Records list (CSV)
                  </button>
                  <button
                    onClick={() => {
                      handleExportParametersCSV();
                      setExportDropdownOpen(false);
                    }}
                    className="w-full text-left px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-teal-50 hover:text-teal-800 flex items-center gap-2 transition"
                    id="btn-export-params-csv"
                  >
                    <FileText className="w-3.5 h-3.5 text-teal-600" />
                    Clinical Bio-markers (CSV)
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="bg-white border border-gray-100 rounded-xl p-20 flex justify-center items-center">
          <Clock className="w-8 h-8 text-teal-600 animate-spin" />
        </div>
      ) : filteredRecords.length > 0 ? (
        /* Logs table */
        <div className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden" id="records-table-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                  <th className="px-6 py-4">Document Details</th>
                  <th className="px-6 py-4">Filing Date</th>
                  <th className="px-6 py-4">Biomarkers Detected</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredRecords.map((record) => {
                  const paramCount = record.extracted_entities ? Object.keys(record.extracted_entities).length : 0;
                  return (
                    <tr 
                      key={record.record_id}
                      onClick={() => onSelectRecord(record.record_id)}
                      className="hover:bg-teal-50/10 cursor-pointer transition text-sm"
                    >
                      <td className="px-6 py-4 flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
                          {record.record_type === 'LAB_REPORT' ? 'LR' : record.record_type === 'PRESCRIPTION' ? 'PR' : 'DN'}
                        </div>
                        <div>
                          <p className="font-bold text-gray-800">{record.record_type.replace('_', ' ')}</p>
                          <p className="text-xs text-gray-400 font-medium">ID: {record.record_id.substring(0, 8)}...</p>
                        </div>
                      </td>

                      <td className="px-6 py-4 text-gray-600 font-semibold text-xs">
                        {new Date(record.report_date).toLocaleDateString()}
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-teal-700 bg-teal-50 px-2.5 py-0.5 rounded-full">
                            {paramCount} clinical metrics
                          </span>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          record.is_processed 
                            ? 'bg-green-50 border-green-200 text-green-700' 
                            : 'bg-yellow-50 border-yellow-200 text-yellow-700'
                        }`}>
                          {record.is_processed ? 'PROCESSED' : 'PROCESSING'}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); onSelectRecord(record.record_id); }}
                            className="p-1.5 text-gray-400 hover:text-teal-600 border border-gray-100 rounded hover:bg-gray-50 transition"
                            title="Inspect extraction data"
                            id={`btn-view-details-${record.record_id}`}
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          
                          <button
                            onClick={(e) => handleDelete(record.record_id, e)}
                            className="p-1.5 text-gray-400 hover:text-red-600 border border-gray-100 rounded hover:bg-gray-50 transition"
                            title="Delete file & data"
                            id={`btn-delete-record-${record.record_id}`}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-dashed border-gray-200 rounded-xl p-16 text-center shadow-sm">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4 animate-pulse" />
          <h3 className="text-lg font-bold text-gray-800">No matching medical records found</h3>
          <p className="text-sm text-gray-500 mt-1 max-w-sm mx-auto">
            Try loosening your filters or search terms, or head to the Ingestion Center to upload a new clinical blood test or doctor note.
          </p>
        </div>
      )}
    </div>
  );
};
