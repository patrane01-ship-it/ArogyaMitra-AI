import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceArea,
} from 'recharts';
import { formatDate } from '../utils/formatDate';

export default function HealthTimeline({ historyData }) {
  if (!historyData || !historyData.readings || historyData.readings.length === 0) {
    return (
      <div className="p-8 text-center bg-gray-50 rounded-2xl border border-gray-100">
        <p className="text-sm text-gray-500">
          No historical readings available for this parameter yet.
        </p>
      </div>
    );
  }

  const { param_name, unit, reference_range_min, reference_range_max, readings } = historyData;

  const chartData = readings.map((r) => ({
    date: formatDate(r.report_date),
    value: r.value,
    status: r.status,
    rawDate: r.report_date,
  }));

  // Min and max for Y-Axis
  const values = readings.map((r) => r.value);
  if (reference_range_min) values.push(reference_range_min);
  if (reference_range_max) values.push(reference_range_max);

  const minY = Math.floor(Math.min(...values) * 0.85);
  const maxY = Math.ceil(Math.max(...values) * 1.15);

  return (
    <div className="glass-card rounded-2xl p-6 border border-gray-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-gray-100 gap-2">
        <div>
          <h3 className="text-lg font-bold text-gray-900 tracking-tight">
            {param_name} <span className="text-sm font-normal text-gray-500">({unit})</span>
          </h3>
          <p className="text-xs text-gray-500">
            Standard Reference Range:{' '}
            <span className="font-mono font-medium text-gray-700">
              {reference_range_min ?? 'N/A'} - {reference_range_max ?? 'N/A'} {unit}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-primary" />
            <span className="text-gray-600">Patient Value</span>
          </div>
          {reference_range_min !== null && reference_range_max !== null && (
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-100 border border-emerald-300" />
              <span className="text-gray-600">Optimal Range</span>
            </div>
          )}
        </div>
      </div>

      <div className="w-full h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis dataKey="date" stroke="#718096" fontSize={12} tickLine={false} />
            <YAxis
              domain={[minY, maxY]}
              stroke="#718096"
              fontSize={12}
              tickLine={false}
              unit={` ${unit}`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 rounded-xl shadow-lg border border-gray-100 text-xs">
                      <p className="font-semibold text-gray-800">{data.date}</p>
                      <p className="text-primary font-mono font-bold mt-1">
                        {data.value} {unit}
                      </p>
                      <span className="inline-block mt-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                        {data.status}
                      </span>
                    </div>
                  );
                }
                return null;
              }}
            />

            {/* Shaded Reference Range */}
            {reference_range_min !== null && reference_range_max !== null && (
              <ReferenceArea
                y1={reference_range_min}
                y2={reference_range_max}
                fill="#4ECBA0"
                fillOpacity={0.15}
                stroke="#4ECBA0"
                strokeDasharray="4 4"
                strokeWidth={1}
              />
            )}

            <Line
              type="monotone"
              dataKey="value"
              stroke="#1A6B5A"
              strokeWidth={3}
              dot={{ stroke: '#1A6B5A', strokeWidth: 2, r: 4, fill: '#FFFFFF' }}
              activeDot={{ r: 6, fill: '#4ECBA0' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
