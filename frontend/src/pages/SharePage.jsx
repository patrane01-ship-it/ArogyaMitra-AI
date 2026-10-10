import React, { useState, useEffect } from 'react';
import { Shield, FileText, AlertCircle, Clock } from 'lucide-react';
import { getSharedResource } from '../services/api';
import { formatDate, formatDateTime } from '../utils/formatDate';

export default function SharePage({ token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchShared = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getSharedResource(token);
        setData(res);
      } catch (err) {
        if (err.response?.status === 410) {
          setError('This clinical consultation link has expired.');
        } else {
          setError('Invalid or corrupted share link.');
        }
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchShared();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-semibold text-gray-600">Verifying signed access token...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background p-4">
        <div className="glass-card rounded-2xl max-w-md w-full p-8 text-center border border-red-200">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-gray-900">Access Restricted</h2>
          <p className="text-xs text-gray-600 mt-2">{error}</p>
          <p className="text-[11px] text-gray-400 mt-4">
            Please ask the patient to generate a fresh consultation link.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-10 px-4 sm:px-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Physician Header */}
        <div className="glass-card rounded-2xl p-6 border border-primary/20 bg-gradient-to-r from-primary/5 via-white to-accent/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary text-white flex items-center justify-center">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs font-bold text-primary uppercase tracking-wider">
                  Physician Consultation Portal
                </span>
                <h1 className="text-xl font-bold text-gray-900">
                  ArogyaMitra AI Clinical Summary
                </h1>
              </div>
            </div>

            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 font-semibold border border-emerald-200">
              Verified Session
            </span>
          </div>
        </div>

        {/* Doctor Report Body */}
        {data.type === 'doctor_report' ? (
          <div className="glass-card rounded-2xl p-6 sm:p-8 border border-gray-200 shadow-sm space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 text-xs text-gray-500">
              <span>Report ID: {data.resource_id.slice(0, 8)}</span>
              <span>Generated: {formatDateTime(data.generated_at)}</span>
            </div>

            <div className="prose prose-sm max-w-none text-gray-800 leading-relaxed space-y-4">
              {data.content.split('\n\n').map((paragraph, idx) => {
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
          </div>
        ) : (
          <div className="glass-card rounded-2xl p-6 border border-gray-200">
            <h3 className="text-sm font-bold text-gray-900 mb-2">
              Shared Record ({data.record_type})
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              Report Date: {formatDate(data.report_date)}
            </p>

            {data.extracted_entities?.parameters && (
              <div className="space-y-2">
                {data.extracted_entities.parameters.map((p, i) => (
                  <div key={i} className="p-2.5 rounded-lg bg-gray-50 border border-gray-100 flex justify-between text-xs">
                    <span className="font-semibold text-gray-800">{p.name}</span>
                    <span className="font-mono text-primary font-bold">{p.value} {p.unit}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="text-center text-[11px] text-gray-400">
          ArogyaMitra AI Secure Clinical Link — Encrypted and Confidential.
        </div>
      </div>
    </div>
  );
}
