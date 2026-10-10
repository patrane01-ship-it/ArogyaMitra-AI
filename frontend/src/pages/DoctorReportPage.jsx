import React, { useState, useEffect } from 'react';
import {
  FileText,
  Sparkles,
  Download,
  Share2,
  Check,
  Copy,
  AlertTriangle,
  Clock,
  Shield,
} from 'lucide-react';
import {
  generateDoctorReport,
  getLatestReport,
  downloadReportPdf,
  generateShareLink,
} from '../services/api';
import { formatDate, formatDateTime } from '../utils/formatDate';

export default function DoctorReportPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  // Share state
  const [shareUrl, setShareUrl] = useState(null);
  const [sharing, setSharing] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLatestReport();
      setReport(data);
    } catch (err) {
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await generateDoctorReport();
      await fetchReport();
    } catch (err) {
      setError(
        err.response?.data?.message ||
          'Failed to generate doctor report. Ensure you have uploaded at least one health record.'
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!report?.report_id) return;
    try {
      const blob = await downloadReportPdf(report.report_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `arogya_doctor_report_${report.report_id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert('Failed to download PDF report.');
    }
  };

  const handleShare = async () => {
    if (!report?.report_id) return;
    setSharing(true);
    try {
      const res = await generateShareLink(report.report_id, 24);
      const fullUrl = `${window.location.origin}${res.share_url}`;
      setShareUrl(fullUrl);
    } catch (e) {
      alert('Failed to generate share link.');
    } finally {
      setSharing(false);
    }
  };

  const handleCopyLink = () => {
    if (!shareUrl) return;
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-primary" /> Doctor-Prep Consultation Report
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            1-Click clinical summary with flagged trends, active medications, and targeted doctor questions
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent-dark hover:from-primary-dark hover:to-primary text-white font-bold text-xs sm:text-sm shadow-md shadow-primary/20 transition-all disabled:opacity-50"
        >
          <Sparkles className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
          {generating ? 'Drafting Clinical Dossier...' : 'Generate Pre-Visit Report'}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Report Content Card */}
      {loading ? (
        <div className="p-12 text-center text-xs text-gray-500 glass-card rounded-2xl">
          Loading report preview...
        </div>
      ) : !report ? (
        <div className="glass-card rounded-2xl p-10 text-center border-dashed border-2 border-gray-200">
          <Shield className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-gray-800">No Doctor-Prep Report Yet</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            Click "Generate Pre-Visit Report" above to compile your lab results, prescriptions, and biometric trajectory into an executive consultation dossier.
          </p>
        </div>
      ) : (
        <div className="glass-card rounded-2xl p-6 sm:p-8 border border-gray-200 shadow-sm space-y-6">
          {/* Action Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-gray-100 gap-3">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Clock className="w-4 h-4 text-gray-400" />
              <span>Generated {formatDateTime(report.generated_at)}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadPdf}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
              >
                <Download className="w-3.5 h-3.5" /> Download PDF
              </button>

              <button
                onClick={handleShare}
                disabled={sharing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-primary bg-primary/10 hover:bg-primary/15 transition-colors"
              >
                <Share2 className="w-3.5 h-3.5" />
                {sharing ? 'Generating link...' : 'Share Link'}
              </button>
            </div>
          </div>

          {/* Share Link Banner */}
          {shareUrl && (
            <div className="p-3.5 rounded-xl bg-teal-50 border border-teal-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 text-teal-900 truncate">
                <span className="font-bold">Share Link (Expires in 24h):</span>
                <span className="font-mono text-gray-600 truncate max-w-xs">{shareUrl}</span>
              </div>
              <button
                onClick={handleCopyLink}
                className="flex items-center gap-1 px-3 py-1 rounded-lg bg-primary text-white font-semibold text-xs shrink-0"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy Link'}
              </button>
            </div>
          )}

          {/* Report Markdown Body */}
          <div className="prose prose-sm max-w-none text-gray-800 leading-relaxed space-y-4">
            {report.report_content.split('\n\n').map((paragraph, idx) => {
              const clean = paragraph.trim();
              if (clean.startsWith('###') || clean.startsWith('##')) {
                return (
                  <h3
                    key={idx}
                    className="text-base font-bold text-primary mt-6 pt-3 border-t border-gray-100 first:border-none first:pt-0"
                  >
                    {clean.replace(/^#+\s*/, '')}
                  </h3>
                );
              }
              return (
                <p key={idx} className="text-xs sm:text-sm text-gray-700">
                  {clean}
                </p>
              );
            })}
          </div>

          {/* Medical Notice */}
          <div className="pt-4 border-t border-gray-100 text-[11px] text-gray-400 italic">
            Notice: This document is an automated clinical summary prepared by ArogyaMitra AI for patient-doctor communication. It is not a formal medical diagnosis.
          </div>
        </div>
      )}
    </div>
  );
}
