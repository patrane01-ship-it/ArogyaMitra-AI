import React, { useState } from 'react';
import { UploadCloud, PenTool, ArrowLeft } from 'lucide-react';
import FileUploader from '../components/FileUploader';
import ManualEntryForm from '../components/ManualEntryForm';

export default function UploadPage({ setActivePage }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'manual'

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => setActivePage('dashboard')}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-primary font-medium mb-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </button>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">
            Add Medical Records
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Ingest lab panels, doctor prescriptions, or manually log daily vitals
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('upload')}
          className={`flex items-center gap-2 py-3 px-5 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'upload'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <UploadCloud className="w-4 h-4" /> Upload Document (PDF / Image)
        </button>
        <button
          onClick={() => setActiveTab('manual')}
          className={`flex items-center gap-2 py-3 px-5 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'manual'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <PenTool className="w-4 h-4" /> Manual Parameter Entry
        </button>
      </div>

      {/* Content */}
      <div className="mt-4">
        {activeTab === 'upload' ? (
          <FileUploader
            onUploadSuccess={() => {
              setTimeout(() => setActivePage('dashboard'), 1500);
            }}
          />
        ) : (
          <ManualEntryForm
            onSuccess={() => {
              setTimeout(() => setActivePage('dashboard'), 1500);
            }}
          />
        )}
      </div>
    </div>
  );
}
