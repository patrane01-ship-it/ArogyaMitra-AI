import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, RefreshCw } from 'lucide-react';
import { getRiskColor } from '../utils/riskColors';

export default function RiskGauge({ riskData, onRecompute, isRecomputing }) {
  if (!riskData || riskData.status === 'no_data') {
    return (
      <div className="glass-card rounded-2xl p-6 text-center border-dashed border-2 border-gray-200">
        <ShieldCheck className="w-12 h-12 text-primary/40 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-gray-800">No Health Risk Computed Yet</h3>
        <p className="text-sm text-gray-500 mt-1 max-w-sm mx-auto">
          Upload your first lab report or enter your medical parameters to generate your comprehensive health score.
        </p>
      </div>
    );
  }

  const score = riskData.overall_risk ?? 0;
  const percentage = Math.round(score * 100);
  const riskLevel = riskData.risk_level || 'LOW';
  const colorMeta = getRiskColor(riskLevel);

  // SVG Gauge calculations (semi-circular dial 180 degrees)
  const radius = 80;
  const strokeWidth = 14;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (score * circumference);

  return (
    <div className="glass-card rounded-2xl p-6 shadow-sm border border-gray-200/80">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
            Health Intelligence Dial
          </h2>
          <p className="text-xs text-gray-500">
            Real-time aggregate risk across all tracked clinical parameters
          </p>
        </div>
        {onRecompute && (
          <button
            onClick={onRecompute}
            disabled={isRecomputing}
            className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary-dark hover:bg-primary/5 px-2.5 py-1.5 rounded-lg border border-primary/20 transition-all disabled:opacity-50"
            title="Force recompute health risk assessment"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRecomputing ? 'animate-spin' : ''}`} />
            {isRecomputing ? 'Scoring...' : 'Recalculate'}
          </button>
        )}
      </div>

      {/* SVG Semi-Circle Dial */}
      <div className="flex flex-col items-center justify-center my-4">
        <div className="relative w-56 h-32 flex items-center justify-center">
          <svg className="w-56 h-36 overflow-visible" viewBox="0 0 200 110">
            <defs>
              <linearGradient id="riskGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10B981" />
                <stop offset="35%" stopColor="#4ECBA0" />
                <stop offset="65%" stopColor="#F5A623" />
                <stop offset="100%" stopColor="#E53E3E" />
              </linearGradient>
            </defs>

            {/* Background Track */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#E2E8F0"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />

            {/* Value Arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="url(#riskGradient)"
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          {/* Centered Readout */}
          <div className="absolute bottom-0 text-center flex flex-col items-center">
            <span className="font-mono text-3xl font-extrabold tracking-tight text-gray-900">
              {percentage}%
            </span>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider mt-1 border ${colorMeta.bg}`}
            >
              {riskLevel} RISK
            </span>
          </div>
        </div>
      </div>

      {/* Contributing Factors */}
      {riskData.contributing_factors && riskData.contributing_factors.length > 0 && (
        <div className="mt-5 pt-4 border-t border-gray-100">
          <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider block mb-2.5">
            Key Contributing Factors
          </span>
          <div className="space-y-2">
            {riskData.contributing_factors.slice(0, 3).map((f, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-xs p-2 rounded-lg bg-gray-50 border border-gray-100"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      f.status === 'CRITICAL'
                        ? 'bg-red-500'
                        : f.status === 'HIGH'
                        ? 'bg-amber-500'
                        : 'bg-blue-500'
                    }`}
                  />
                  <span className="font-medium text-gray-800">{f.param_name}</span>
                  <span className="font-mono text-gray-500">
                    {f.value} {f.unit}
                  </span>
                </div>
                <span className="font-mono text-[11px] font-semibold text-gray-700 bg-white px-2 py-0.5 rounded border border-gray-200">
                  +{Math.round(f.weight * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {riskData.recommendations && riskData.recommendations.length > 0 && (
        <div className="mt-4 p-3 rounded-xl bg-teal-50/60 border border-teal-100 text-xs text-teal-900">
          <p className="font-medium flex items-center gap-1.5 text-primary-dark mb-1">
            <AlertTriangle className="w-3.5 h-3.5 text-primary" />
            AI Guidance
          </p>
          <p className="text-gray-700 leading-relaxed">
            {riskData.recommendations[0]}
          </p>
        </div>
      )}
    </div>
  );
}
