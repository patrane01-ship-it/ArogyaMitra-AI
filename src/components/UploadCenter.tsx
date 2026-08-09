import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw, 
  Calendar, 
  Clipboard, 
  ArrowRight 
} from 'lucide-react';
import { api } from '../services/api.ts';
import { RecordType } from '../types.ts';

interface UploadCenterProps {
  onProcessingComplete: (recordId: string) => void;
  onNavigate: (tab: string) => void;
}

export const UploadCenter: React.FC<UploadCenterProps> = ({ onProcessingComplete, onNavigate }) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'manual'>('upload');
  
  // File upload state
  const [file, setFile] = useState<File | null>(null);
  const [recordType, setRecordType] = useState<RecordType>('LAB_REPORT');
  const [reportDate, setReportDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [isDragging, setIsDragging] = useState(false);
  
  // Manual entry state
  const [manualText, setManualText] = useState('');
  
  // Submission & Processing state
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [successRecord, setSuccessRecord] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(selectedFile.type)) {
      setErrorMsg('Unsupported file format. Please upload a PDF or JPG/PNG image.');
      setFile(null);
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setErrorMsg('File exceeds 10MB limit. Please upload a smaller document.');
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setErrorMsg(null);

    // Auto-detect record type based on filename hints
    const lowerName = selectedFile.name.toLowerCase();
    if (lowerName.includes('prescrip') || lowerName.includes('rx') || lowerName.includes('med')) {
      setRecordType('PRESCRIPTION');
    } else if (lowerName.includes('note') || lowerName.includes('doctor')) {
      setRecordType('DOCTOR_NOTE');
    } else if (lowerName.includes('imaging') || lowerName.includes('xray') || lowerName.includes('scan')) {
      setRecordType('IMAGING');
    } else {
      setRecordType('LAB_REPORT');
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleSubmitFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setErrorMsg(null);
    setProgressMsg('Uploading encrypted file securely...');

    try {
      // Simulate real step updates for excellent visual feedback
      setTimeout(() => setProgressMsg('Running AI-driven medical OCR text transcription...'), 1200);
      setTimeout(() => setProgressMsg('Decrypting, extracting and standardizing 15 key biomarkers...'), 3000);
      setTimeout(() => setProgressMsg('Running Trend Engine & evaluating overall risk metric...'), 4500);

      const record = await api.uploadRecord(file, recordType, new Date(reportDate).toISOString());
      
      setProgressMsg('Ingestion complete!');
      setSuccessRecord(record);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Processing failed. Please verify API key and credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualText.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    setProgressMsg('Analyzing pasted text structure...');

    try {
      setTimeout(() => setProgressMsg('Extracting bio-markers & creating clinical entities...'), 1200);
      
      const record = await api.uploadRecord(null, recordType, new Date(reportDate).toISOString(), manualText);
      
      setProgressMsg('Extraction complete!');
      setSuccessRecord(record);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Manual entry analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setManualText('');
    setSuccessRecord(null);
    setErrorMsg(null);
    setProgressMsg('');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6" id="upload-center-view">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 font-serif">Arogya Ingestion Terminal</h2>
        <p className="text-gray-500 mt-1">Upload files or write clinical notes to extract health bio-markers securely.</p>
      </div>

      {/* Tabs */}
      {!successRecord && !loading && (
        <div className="flex border-b border-gray-100 bg-white p-1 rounded-xl shadow-sm border" id="upload-tabs">
          <button
            onClick={() => { setActiveTab('upload'); setErrorMsg(null); }}
            className={`flex-1 py-3 text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'upload' 
                ? 'bg-teal-50 text-teal-800' 
                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <Upload className="w-4 h-4" />
            File Upload (OCR)
          </button>
          <button
            onClick={() => { setActiveTab('manual'); setErrorMsg(null); }}
            className={`flex-1 py-3 text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'manual' 
                ? 'bg-teal-50 text-teal-800' 
                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <Clipboard className="w-4 h-4" />
            Paste Clinical Text
          </button>
        </div>
      )}

      {/* Main Container */}
      <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm">
        <AnimatePresence mode="wait">
          {loading ? (
            /* Loading Processing Screen */
            <motion.div 
              key="loading"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-16 text-center"
              id="processing-panel"
            >
              <div className="relative w-20 h-20 mb-6">
                <div className="absolute inset-0 rounded-full border-4 border-teal-50"></div>
                <div className="absolute inset-0 rounded-full border-4 border-t-teal-600 animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <FileText className="w-8 h-8 text-teal-600" />
                </div>
              </div>
              <h3 className="text-lg font-bold text-gray-800">Processing Your Clinical Document</h3>
              <p className="text-sm text-teal-600 font-medium mt-2 animate-pulse">{progressMsg}</p>
              <p className="text-xs text-gray-400 mt-6 max-w-sm">
                ArogyaMitra secures files with AES-256-GCM before submitting them to our private Gemini 3.6 processing node.
              </p>
            </motion.div>
          ) : successRecord ? (
            /* Success Feedback screen */
            <motion.div 
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="py-8 text-center space-y-6"
              id="success-panel"
            >
              <div className="w-16 h-16 bg-green-50 border border-green-200 rounded-full flex items-center justify-center mx-auto text-green-600">
                <CheckCircle className="w-10 h-10" />
              </div>
              
              <div>
                <h3 className="text-xl font-bold text-gray-900">Health Record Processed Successfully!</h3>
                <p className="text-sm text-gray-500 mt-1">
                  We processed your document from {new Date(successRecord.report_date).toLocaleDateString()}
                </p>
              </div>

              {/* Little summary card */}
              <div className="bg-gray-50 rounded-xl p-4 text-left border border-gray-100 max-w-md mx-auto">
                <span className="text-xs font-bold uppercase tracking-wider text-teal-700 block mb-1">
                  Extracted Biomarkers
                </span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {successRecord.extracted_entities && Object.keys(successRecord.extracted_entities).length > 0 ? (
                    Object.entries(successRecord.extracted_entities).map(([name, val]: any) => (
                      <span key={name} className="bg-white border border-gray-200 text-xs px-2.5 py-1 rounded-md font-medium text-gray-700">
                        {name}: <strong className="text-teal-700 font-bold">{val}</strong>
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-500 italic">No exact bio-markers detected. General records saved successfully.</span>
                  )}
                </div>
              </div>

              <div className="flex justify-center gap-4 pt-4">
                <button
                  onClick={handleReset}
                  className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-700 font-medium transition"
                  id="btn-upload-another"
                >
                  Upload Another
                </button>
                <button
                  onClick={() => onProcessingComplete(successRecord.record_id)}
                  className="px-5 py-2 bg-teal-700 text-white font-semibold rounded-lg hover:bg-teal-800 transition flex items-center gap-1.5 shadow-sm"
                  id="btn-view-extracted"
                >
                  View Extracted Results
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ) : (
            /* Input Forms */
            <motion.div
              key="form"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {errorMsg && (
                <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-xl flex gap-3 text-sm mb-6" id="upload-error">
                  <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">Processing Failed</p>
                    <p className="text-red-700 mt-0.5">{errorMsg}</p>
                  </div>
                </div>
              )}

              {/* Standard Options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Record Classification</label>
                  <select
                    value={recordType}
                    onChange={(e) => setRecordType(e.target.value as RecordType)}
                    className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500"
                    id="select-record-type"
                  >
                    <option value="LAB_REPORT">Lab Blood Report</option>
                    <option value="PRESCRIPTION">Doctor Prescription</option>
                    <option value="DOCTOR_NOTE">Physician Notes / Summary</option>
                    <option value="IMAGING">Imaging Report (X-Ray, MRI)</option>
                    <option value="MANUAL_ENTRY">Manual Bio-Marker Logging</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Report / Consultation Date</label>
                  <div className="relative">
                    <Calendar className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" />
                    <input
                      type="date"
                      value={reportDate}
                      max={new Date().toISOString().split('T')[0]}
                      onChange={(e) => setReportDate(e.target.value)}
                      className="w-full pl-10 pr-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500"
                      id="input-report-date"
                    />
                  </div>
                </div>
              </div>

              {activeTab === 'upload' ? (
                /* Drag and drop file uploader */
                <form onSubmit={handleSubmitFile} className="space-y-6">
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={triggerFileInput}
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${
                      isDragging 
                        ? 'border-teal-500 bg-teal-50/20' 
                        : file 
                        ? 'border-green-300 bg-green-50/10' 
                        : 'border-gray-200 hover:border-teal-400 bg-gray-50/50'
                    }`}
                    id="dropzone"
                  >
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      accept=".pdf,image/png,image/jpeg,image/jpg"
                      className="hidden"
                    />
                    
                    <div className="w-12 h-12 rounded-full bg-teal-50 flex items-center justify-center mx-auto text-teal-700 mb-4">
                      {file ? <FileText className="w-6 h-6" /> : <Upload className="w-6 h-6" />}
                    </div>

                    {file ? (
                      <div className="space-y-1">
                        <p className="text-sm font-bold text-gray-800 break-all">{file.name}</p>
                        <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB • Ready to analyze</p>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <p className="text-sm font-bold text-gray-800">Drag & drop your health report here, or <span className="text-teal-600 hover:underline">browse</span></p>
                        <p className="text-xs text-gray-500">Supports PDF, PNG, JPG (Max 10MB)</p>
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={!file}
                    className="w-full py-3 bg-teal-700 hover:bg-teal-800 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center justify-center gap-2"
                    id="btn-upload-file-submit"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Process Secure Document
                  </button>
                </form>
              ) : (
                /* Manual Text Ingestion Box */
                <form onSubmit={handleSubmitManual} className="space-y-6">
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                      Raw Clinical Text or Bio-marker Readings
                    </label>
                    <textarea
                      value={manualText}
                      onChange={(e) => setManualText(e.target.value)}
                      placeholder="Example: Blood Sugar Report&#10;FBS: 98 mg/dL&#10;HbA1c: 5.7%&#10;Total Cholesterol: 180 mg/dL"
                      rows={6}
                      className="w-full p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 font-medium font-mono placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500"
                      id="textarea-manual-text"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={!manualText.trim()}
                    className="w-full py-3 bg-teal-700 hover:bg-teal-800 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center justify-center gap-2"
                    id="btn-manual-submit"
                  >
                    <Clipboard className="w-4 h-4" />
                    Extract Bio-markers from Text
                  </button>
                </form>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
