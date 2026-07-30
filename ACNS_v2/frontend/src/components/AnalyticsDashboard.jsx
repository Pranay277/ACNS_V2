import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, AreaChart, Area } from 'recharts';
import Card from './Card';

const COLORS = {
  open: '#ef4444',
  inProgress: '#f59e0b',
  closed: '#22c55e',
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  tertiary: '#ec4899',
  categories: ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#22c55e', '#ef4444'],
};

const AnalyticsDashboard = ({ issues = [] }) => {
  const stats = useMemo(() => {
    const total = issues.length;
    const closed = issues.filter(i => i.status === 'Closed' || i.status === 'Resolved').length;
    const inProgress = issues.filter(i => i.status === 'In Progress').length;
    const open = total - closed - inProgress;

    const categoryCounts = issues.reduce((acc, issue) => {
      const category = issue.category || 'Uncategorized';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});

    const topCategories = Object.entries(categoryCounts)
      .sort(([, a], [, b]) => b - a)
      .map(([name, count]) => ({ name, count }))
      .slice(0, 8);

    const locationCounts = issues.reduce((acc, issue) => {
      const location = issue.location?.text || issue.location || 'Unknown';
      acc[location] = (acc[location] || 0) + 1;
      return acc;
    }, {});

    const topLocations = Object.entries(locationCounts)
      .sort(([, a], [, b]) => b - a)
      .map(([name, count]) => ({ name, count }))
      .slice(0, 3);

    const closedIssues = issues.filter(i => i.status === 'Closed' && i.createdAt && i.updatedAt);
    let avgResolutionTime = 'N/A';
    
    if (closedIssues.length > 0) {
      const totalTime = closedIssues.reduce((sum, issue) => {
        const created = new Date(issue.createdAt);
        const resolved = new Date(issue.updatedAt);
        const diffMs = resolved - created;
        const diffHours = diffMs / (1000 * 60 * 60);
        return sum + diffHours;
      }, 0);
      avgResolutionTime = `${(totalTime / closedIssues.length).toFixed(1)} hours`;
    }

    return {
      total,
      open,
      inProgress,
      closed,
      topCategories,
      topLocations,
      avgResolutionTime,
      statusData: [
        { name: 'Open', value: open, color: COLORS.open },
        { name: 'In Progress', value: inProgress, color: COLORS.inProgress },
        { name: 'Resolved', value: closed, color: COLORS.closed },
      ],
    };
  }, [issues]);

  if (!issues || issues.length === 0) {
    return (
      <Card className="p-12 flex flex-col items-center justify-center text-gray-500">
        <p className="text-lg font-medium text-gray-800">No Analytics Data Available</p>
        <p className="text-sm">Issues must be reported to generate insights.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-2">Total Issues</h3>
          <p className="text-3xl font-extrabold text-gray-900">{stats.total}</p>
        </Card>
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-2">Open Issues</h3>
          <p className="text-3xl font-extrabold text-red-500">{stats.open}</p>
        </Card>
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-2">Closed Issues</h3>
          <p className="text-3xl font-extrabold text-green-500">{stats.closed}</p>
        </Card>
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-2">Avg. Resolution</h3>
          <p className="text-3xl font-extrabold text-blue-500 truncate">{stats.avgResolutionTime}</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Open vs Closed - Using Donut Chart with better styling */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-800">Issue Status Overview</h3>
            <div className="flex gap-3">
              {stats.statusData.map((item) => (
                <div key={item.name} className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-xs text-gray-500">{item.name}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="relative">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <defs>
                  <filter id="shadow">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15"/>
                  </filter>
                </defs>
                <Pie
                  data={stats.statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={85}
                  outerRadius={115}
                  paddingAngle={4}
                  dataKey="value"
                  stroke="none"
                  filter="url(#shadow)"
                >
                  {stats.statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                  itemStyle={{ fontWeight: 600 }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center -mt-2">
              <p className="text-4xl font-bold text-gray-900">{stats.total}</p>
              <p className="text-xs text-gray-500">Total</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4">
            {stats.statusData.map((item) => (
              <div key={item.name} className="text-center p-3 rounded-lg bg-gray-50">
                <p className="text-xl font-bold" style={{ color: item.color }}>{item.value}</p>
                <p className="text-xs text-gray-500">{item.name}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Categories - Using horizontal bars with gradient colors */}
        <Card>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-800">Issues by Category</h3>
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full">
              {stats.topCategories.length} categories
            </span>
          </div>
          <div className="space-y-4">
            {stats.topCategories.map((cat, index) => {
              const percentage = (cat.count / stats.total) * 100;
              return (
                <div key={cat.name}>
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-sm font-medium text-gray-700 truncate flex items-center gap-2">
                      <span 
                        className="w-2 h-2 rounded-full" 
                        style={{ backgroundColor: COLORS.categories[index % COLORS.categories.length] }}
                      />
                      {cat.name}
                    </span>
                    <span className="text-sm font-semibold text-gray-900">{cat.count}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all duration-700 ease-out"
                      style={{ 
                        width: `${percentage}%`,
                        backgroundColor: COLORS.categories[index % COLORS.categories.length]
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="text-lg font-bold text-gray-800 mb-6 border-b border-gray-100 pb-3">Top Hotspot Locations</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stats.topLocations} margin={{ top: 20, right: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#374151', fontSize: 13, fontWeight: 500 }} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280' }} dx={-10} />
            <Tooltip cursor={{ fill: '#F3F4F6' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} />
            <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
            <Bar dataKey="count" fill={COLORS.secondary} radius={[6, 6, 0, 0]} name="Issues Reported" barSize={50} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
};

export default AnalyticsDashboard;
