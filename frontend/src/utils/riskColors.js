export const getRiskColor = (level) => {
  switch (level?.toUpperCase()) {
    case 'LOW':
      return {
        bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        badge: 'bg-emerald-100 text-emerald-800',
        hex: '#10B981',
      };
    case 'MODERATE':
      return {
        bg: 'bg-amber-50 text-amber-700 border-amber-200',
        badge: 'bg-amber-100 text-amber-800',
        hex: '#F5A623',
      };
    case 'HIGH':
      return {
        bg: 'bg-orange-50 text-orange-700 border-orange-200',
        badge: 'bg-orange-100 text-orange-800',
        hex: '#EA580C',
      };
    case 'CRITICAL':
      return {
        bg: 'bg-red-50 text-red-700 border-red-200',
        badge: 'bg-red-100 text-red-800',
        hex: '#E53E3E',
      };
    default:
      return {
        bg: 'bg-gray-50 text-gray-700 border-gray-200',
        badge: 'bg-gray-100 text-gray-800',
        hex: '#6B7280',
      };
  }
};

export const getStatusBadge = (status) => {
  switch (status?.toUpperCase()) {
    case 'NORMAL':
      return 'bg-emerald-100 text-emerald-800 border border-emerald-200';
    case 'LOW':
      return 'bg-blue-100 text-blue-800 border border-blue-200';
    case 'HIGH':
      return 'bg-amber-100 text-amber-800 border border-amber-200';
    case 'CRITICAL':
      return 'bg-rose-100 text-rose-800 border border-rose-300 animate-pulse';
    default:
      return 'bg-gray-100 text-gray-800 border border-gray-200';
  }
};
