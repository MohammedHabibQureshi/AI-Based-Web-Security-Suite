import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  iconColorClass?: string;
  trend?: string;
  trendType?: 'positive' | 'negative' | 'neutral';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  description,
  icon: Icon,
  iconColorClass = 'text-blue-500 bg-blue-500/10',
  trend,
  trendType = 'neutral'
}) => {
  return (
    <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between transition-all duration-300 hover:scale-[1.02] hover:border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2.5 rounded-xl ${iconColorClass}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      
      <div>
        <div className="text-3xl font-bold text-white mb-1">{value}</div>
        <div className="flex items-center space-x-2 text-xs">
          {trend && (
            <span className={`font-semibold ${
              trendType === 'positive' ? 'text-green-500' :
              trendType === 'negative' ? 'text-red-500' : 'text-slate-400'
            }`}>
              {trend}
            </span>
          )}
          {description && <span className="text-slate-500">{description}</span>}
        </div>
      </div>
    </div>
  );
};
export default MetricCard;
