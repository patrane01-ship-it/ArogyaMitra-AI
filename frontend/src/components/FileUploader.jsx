import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle, CheckCircle2, Lock } from 'lucide-react';
import { uploadRecordFile } from '../services/api';

export default function FileUploader({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [recordType, setRecordType] = useState('LAB_REPORT');
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    setError(null);
    if (!selectedFile) return;

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size exceeds maximum allowed 10MB limit');
      return;
    }

    const validTypes = ['application/pdf', 'image/jpeg', 'image/png'];
    if (!validTypes.includes(selectedFile.type)) {
      setError('Only PDF, JPG, and PNG files are supported');
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('record_type', recordType);
    formData.append('report_date', reportDate);

    try {
      const res = await uploadRecordFile(formData);
      setSuccess('Document encrypted and uploaded! AI processing started.');
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      if (onUploadSuccess) onUploadSuccess(res);
    } catch (err) {
      setError(err.response?.data?.message || 'Upload failed. Please check document and try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 border border-gray-200">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Drag and Drop Zone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            dragActive
              ? 'border-accent bg-accent/5'
              : 'border-gray-300 hover:border-primary/50 bg-gray-50/50'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            className="hidden"
            onChange={(e) => validateAndSetFile(e.target.files?.[0])}
          />

          <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>

          <p className="text-sm font-semibold text-gray-800">
            {file ? file.name : 'Click to upload or drag & drop'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Supported: PDF, JPG, PNG (Max 10MB)
          </p>

          <div className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-emerald-700 font-medium">
            <Lock className="w-3.5 h-3.5 text-emerald-600" />
            AES-256-GCM Military Grade At-Rest Encryption
          </div>
        </div>

        {/* Document Metadata Form */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Document Category
            </label>
            <select
              value={recordType}
              onChange={(e) => setRecordType(e.target.value)}
              className="w-full text-xs rounded-xl border border-gray-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              <option value="LAB_REPORT">Lab Report (Blood, Urine, etc.)</option>
              <option value="PRESCRIPTION">Prescription (Rx)</option>
              <option value="DOCTOR_NOTE">Doctor Consultation Note</option>
              <option value="IMAGING">Imaging / Radiology Report</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Date on Document
            </label>
            <input
              type="date"
              value={reportDate}
              max={new Date().toISOString().split('T')[0]}
              onChange={(e) => setReportDate(e.target.value)}
              className="w-full text-xs rounded-xl border border-gray-300 p-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
        </div>

        {/* Status Alerts */}
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

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!file || uploading}
          className="w-full py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-dark text-white font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-primary/20 flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Encrypting & Ingesting...</span>
            </>
          ) : (
            'Encrypt & Upload Report'
          )}
        </button>
      </form>
    </div>
  );
}
