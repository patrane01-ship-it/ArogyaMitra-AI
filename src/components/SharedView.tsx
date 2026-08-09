import React, { useEffect, useState } from 'react';
import Markdown from 'react-markdown';
import { 
  ShieldCheck, 
  Clock, 
  FileText, 
  AlertTriangle, 
  Activity, 
  Calendar, 
  HeartHandshake 
} from 'lucide-react';
import { api } from '../services/api.ts';
import { ClinicalParameter } from '../types.ts';

interface SharedViewProps {
  token: string;
}

export const SharedView: React.FC<SharedViewProps> = ({ token }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sharedData, setSharedData] = useState<any | null>(null);
  const [contentType, setContentType] = useState<'DOCTOR_REPORT' | 'HEALTH_RECORD' | null>(null);
  const [clinicalParams, setClinicalParams] = useState<ClinicalParameter[]>([]);

  useEffect(() => {
    const fetchSharedContent = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getSharedContent(token);
        setContentType(res.type);
        setSharedData(res.data);
        if (res.clinical_parameters) {
          setClinicalParams(res.clinical_parameters);
        }
      } catch (err: any) {
        console.error('Shared content fetching failed:', err);
        setError(err.message || 'This clinical share link is either invalid, tampered, or has expired.');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchSharedContent();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6 text-center">
        <Activity className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-600 font-medium font-serif text-lg">Decrypting shared clinical dossier...</p>
        <p className="text-xs text-gray-400 mt-2">Authenticating token credentials with secure key management...</p>
      </div>
    );
  }

  if (error || !sharedData) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
        <div className="bg-white border border-red-150 p-8 rounded-xl shadow-sm text-center max-w-md space-y-4">
          <div className="w-12 h-12 bg-red-50 text-red-600 border border-red-200 rounded-full flex items-center justify-center mx-auto">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900 font-serif">Secure Link Expired or Invalid</h2>
            <p className="text-sm text-gray-500 mt-2 leading-relaxed">
              For security compliance, ArogyaMitra share links expire automatically. Please request a new compiled sharing link from your patient.
            </p>
          </div>
          {error && <p className="text-xs text-red-700 bg-red-50 p-2.5 rounded-lg font-mono">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-between" id="public-shared-portal">
      {/* Portal Header */}
      <header className="bg-white border-b border-gray-100 py-4 px-6 md:px-12 sticky top-0 z-50 shadow-sm">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold font-serif">
              AM
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900 font-serif leading-none">ArogyaMitra AI</h1>
              <p className="text-[10px] font-bold text-teal-700 uppercase tracking-wider mt-1">Secure Clinical Portal</p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-bold text-teal-800 bg-teal-50 px-3 py-1.5 rounded-lg border border-teal-100 shadow-sm">
            <ShieldCheck className="w-4 h-4 text-teal-600" />
            HIPAA Compliant Viewer
          </div>
        </div>
      </header>

      {/* Main Dossier Content */}
      <main className="flex-grow py-8 px-4 md:px-12 max-w-4xl mx-auto w-full">
        
        <div className="bg-white border border-gray-150 rounded-2xl p-6 md:p-10 shadow-sm space-y-8">
          
          {/* Metadata banner */}
          <div className="border-b border-gray-150 pb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs text-gray-500">
            <div className="space-y-1">
              <p className="font-bold text-gray-400 uppercase tracking-wider">Document Classification</p>
              <p className="text-sm font-extrabold text-teal-900 font-serif">
                {contentType === 'DOCTOR_REPORT' ? 'Physician Pre-Visit Summary Report' : 'Extracted Clinical Health Record'}
              </p>
            </div>

            <div className="space-y-1 sm:text-right">
              <p className="font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1 sm:justify-end">
                <Clock className="w-3 h-3" />
                Dossier Metadata
              </p>
              <p className="font-semibold text-gray-700">
                Compiled: {new Date(sharedData.generated_at || sharedData.upload_date).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Report or Record rendering */}
          {contentType === 'DOCTOR_REPORT' ? (
            /* MD Report */
            <div className="prose prose-teal max-w-none">
              <div className="markdown-body text-gray-800 leading-relaxed space-y-5">
                <Markdown>{sharedData.report_content}</Markdown>
              </div>
            </div>
          ) : (
            /* Individual Health Record read-only */
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-gray-900 font-serif">Record Summary</h3>
                <p className="text-sm text-gray-500 mt-1">Processed from {sharedData.record_type.replace('_', ' ')} dated {new Date(sharedData.report_date).toLocaleDateString()}.</p>
              </div>

              {clinicalParams.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {clinicalParams.map((p) => (
                    <div key={p.param_id} className="p-4 border border-gray-150 bg-white rounded-xl space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-gray-700 text-sm">{p.param_name}</span>
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                          p.status === 'NORMAL' 
                            ? 'bg-green-50 text-green-700 border-green-200' 
                            : p.status === 'LOW' 
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-orange-50 text-orange-700 border-orange-200'
                        }`}>
                          {p.status}
                        </span>
                      </div>
                      <p className="text-2xl font-bold text-gray-900">
                        {p.value} <span className="text-xs text-gray-500 font-normal">{p.unit}</span>
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">No exact bio-markers parsed from this record.</p>
              )}

              {sharedData.raw_text && (
                <div className="border-t border-gray-150 pt-6 mt-6">
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Decrypted OCR Document Text</h4>
                  <pre className="p-4 bg-gray-50 border rounded-lg text-xs text-gray-600 font-mono whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                    {sharedData.raw_text}
                  </pre>
                </div>
              )}
            </div>
          )}

        </div>

      </main>

      {/* Portal Footer */}
      <footer className="bg-white border-t border-gray-100 py-6 px-6 text-center text-xs text-gray-400">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-3">
          <p className="flex items-center gap-1">
            <HeartHandshake className="w-3.5 h-3.5 text-teal-600" />
            Empowering physician-patient collaborative healthcare.
          </p>
          <p className="font-mono text-[10px] uppercase tracking-wider">Secure token identification: {token.substring(0, 16)}...</p>
        </div>
      </footer>
    </div>
  );
};
