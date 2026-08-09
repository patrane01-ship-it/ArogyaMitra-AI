import React, { useEffect, useState } from 'react';
import Markdown from 'react-markdown';
import { motion, AnimatePresence } from 'motion/react';
import { 
  FileText, 
  RefreshCw, 
  Download, 
  Share2, 
  Calendar, 
  Check, 
  Clock, 
  Copy, 
  AlertTriangle, 
  Eye, 
  Link 
} from 'lucide-react';
import { api } from '../services/api.ts';
import { DoctorReport } from '../types.ts';

export const DoctorPrep: React.FC = () => {
  const [report, setReport] = useState<DoctorReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sharing states
  const [expiryHours, setExpiryHours] = useState<number>(24);
  const [shareLink, setShareLink] = useState<string>('');
  const [shareExpires, setShareExpires] = useState<string>('');
  const [creatingShare, setCreatingShare] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchLatestReport = async () => {
    try {
      const data = await api.getLatestDoctorReport();
      setReport(data);
      setError(null);
    } catch (err: any) {
      if (err.status === 404) {
        // No report generated yet
        setReport(null);
      } else {
        console.error('Failed to load report:', err);
        setError('Could not retrieve existing pre-visit summaries.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestReport();
  }, []);

  const handleGenerateReport = async () => {
    setGenerating(true);
    setError(null);
    try {
      const newReport = await api.generateDoctorReport();
      setReport(newReport);
      // Reset share link if generated a new report
      setShareLink('');
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Generation failed. Make sure you have uploaded at least one clinical record.');
    } finally {
      setGenerating(false);
    }
  };

  const handleCreateShareLink = async () => {
    if (!report) return;
    setCreatingShare(true);
    setCopied(false);
    try {
      const res = await api.createShareLink(report.report_id, expiryHours);
      // Build absolute client-side URL using current location hash pattern
      const absoluteUrl = `${window.location.origin}/#/share/${res.share_token}`;
      setShareLink(absoluteUrl);
      setShareExpires(res.expires_at);
    } catch (err: any) {
      alert('Failed to generate share token: ' + err.message);
    } finally {
      setCreatingShare(false);
    }
  };

  const handleCopyLink = () => {
    if (!shareLink) return;
    navigator.clipboard.writeText(shareLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-100 rounded-xl p-20 flex flex-col justify-center items-center">
        <RefreshCw className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-500 font-medium">Retrieving latest pre-visit reports...</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8" id="doctor-prep-view">
      
      {/* Left Panel: Markdown Report & Controls */}
      <div className="lg:col-span-8 space-y-6">
        
        {/* Banner with Generate trigger */}
        <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <FileText className="w-5 h-5 text-teal-600" />
              Doctor Pre-Visit Summarizer
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {report 
                ? `Last compiled on ${new Date(report.generated_at).toLocaleDateString()}` 
                : 'Compile an intelligence summary from blood tests and prescriptions.'
              }
            </p>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="px-5 py-2.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold rounded-lg transition disabled:opacity-50 flex items-center gap-2 shadow-sm text-sm shrink-0"
            id="btn-generate-report"
          >
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {report ? 'Recompile Report' : 'Compile Pre-Visit Report'}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-xl flex gap-3 text-sm" id="report-error">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Synthesis Incomplete</p>
              <p className="text-red-700 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {generating ? (
          /* Generate Loading State */
          <div className="bg-white border border-gray-100 rounded-xl p-16 text-center space-y-4 shadow-sm" id="report-generating-screen">
            <div className="relative w-16 h-16 mx-auto mb-2">
              <div className="absolute inset-0 rounded-full border-4 border-teal-50"></div>
              <div className="absolute inset-0 rounded-full border-4 border-t-teal-600 animate-spin"></div>
            </div>
            <h3 className="text-lg font-bold text-gray-800">Synthesizing Clinical Records...</h3>
            <p className="text-sm text-teal-600 font-medium animate-pulse">Running Doctor Prep agent cluster...</p>
            <p className="text-xs text-gray-400 max-w-sm mx-auto">
              We are analyzing your historical clinical parameters, calculating trend rates, sorting medications, and structuring questions to prepare your doctor.
            </p>
          </div>
        ) : report ? (
          /* Markdown Report Viewer */
          <div className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden" id="report-viewer-panel">
            <div className="bg-gray-50 border-b border-gray-100 px-6 py-4 flex justify-between items-center">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Report Output (Markdown)</span>
              
              {/* PDF Download link */}
              <a
                href={`/api/report/${report.report_id}/pdf`}
                target="_blank"
                rel="noreferrer"
                className="px-3.5 py-1.5 bg-white border border-gray-200 hover:border-teal-500 rounded-lg text-xs font-bold text-gray-700 hover:text-teal-700 flex items-center gap-1.5 transition shadow-sm"
                id="btn-download-pdf"
              >
                <Download className="w-3.5 h-3.5" />
                Download PDF
              </a>
            </div>

            <div className="px-8 py-8 prose prose-teal max-w-none max-h-[600px] overflow-y-auto" id="report-content-body">
              <div className="markdown-body text-gray-800 leading-relaxed space-y-4">
                <Markdown>{report.report_content}</Markdown>
              </div>
            </div>
          </div>
        ) : (
          /* Empty Report State */
          <div className="bg-white border border-dashed border-gray-200 rounded-xl p-16 text-center shadow-sm">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4 animate-pulse" />
            <h3 className="text-lg font-bold text-gray-800">No Pre-Visit Summary Synthesized</h3>
            <p className="text-sm text-gray-500 mt-1 max-w-sm mx-auto">
              Compile your health records into a clean, concise dossier that you can present to your consulting general physician.
            </p>
            <button
              onClick={handleGenerateReport}
              className="mt-6 px-5 py-2.5 bg-teal-700 text-white font-semibold rounded-lg hover:bg-teal-800 transition shadow-sm text-sm inline-flex items-center gap-2"
              id="btn-quick-generate"
            >
              <RefreshCw className="w-4 h-4" />
              Compile Report Now
            </button>
          </div>
        )}
      </div>

      {/* Right Panel: Expiry Sharing Engine */}
      {report && !generating && (
        <div className="lg:col-span-4 bg-white border border-gray-100 rounded-xl p-6 shadow-sm space-y-6" id="report-sharing-panel">
          <div>
            <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wider flex items-center gap-2">
              <Share2 className="w-4.5 h-4.5 text-teal-600" />
              Secure Clinical Share Link
            </h3>
            <p className="text-xs text-gray-500 mt-1">Generate a read-only secure URL with custom duration expiry for your physician.</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Token Lifespan Expiry</label>
              <div className="grid grid-cols-4 gap-1.5 p-1 bg-gray-50 border border-gray-150 rounded-lg">
                {[1, 12, 24, 72].map(hrs => (
                  <button
                    key={hrs}
                    onClick={() => { setExpiryHours(hrs); setShareLink(''); }}
                    className={`py-1.5 text-xs font-semibold rounded transition ${
                      expiryHours === hrs 
                        ? 'bg-teal-700 text-white font-bold' 
                        : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100/50'
                    }`}
                    id={`btn-expiry-option-${hrs}`}
                  >
                    {hrs}h
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleCreateShareLink}
              disabled={creatingShare}
              className="w-full py-2.5 bg-gray-50 hover:bg-gray-100 text-gray-700 border border-gray-200 hover:border-teal-500 font-bold rounded-lg transition text-xs flex items-center justify-center gap-1.5 shadow-sm"
              id="btn-generate-share-link"
            >
              <Link className="w-3.5 h-3.5 text-teal-600" />
              {creatingShare ? 'Securing URL...' : 'Generate Securing URL'}
            </button>

            <AnimatePresence>
              {shareLink && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="space-y-3.5 border-t border-gray-100 pt-4"
                  id="share-link-result"
                >
                  <div className="p-3 bg-teal-50/40 border border-teal-100 rounded-lg space-y-1.5">
                    <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wide flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Active Link (Expires: {new Date(shareExpires).toLocaleString()})
                    </span>
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        readOnly
                        value={shareLink}
                        className="w-full bg-white border border-gray-200 rounded p-1.5 text-xs text-gray-600 focus:outline-none font-mono text-ellipsis overflow-hidden whitespace-nowrap"
                      />
                      <button
                        onClick={handleCopyLink}
                        className={`p-1.5 border rounded shrink-0 transition ${
                          copied 
                            ? 'bg-green-50 border-green-200 text-green-700' 
                            : 'bg-white border-gray-200 hover:border-teal-500 text-gray-600'
                        }`}
                        title="Copy Share Link"
                        id="btn-copy-share-link"
                      >
                        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  <a 
                    href={shareLink}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2 bg-teal-50 hover:bg-teal-100 text-teal-800 font-semibold rounded-lg text-xs flex items-center justify-center gap-1 transition border border-teal-100"
                    id="btn-preview-share-link"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Preview Doctor View
                  </a>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

    </div>
  );
};
