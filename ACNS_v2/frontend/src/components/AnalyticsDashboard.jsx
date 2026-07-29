import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import Card from './Card';

const COLORS = {
  open: '#ef4444',
  closed: '#22c55e',
  primary: '#3b82f6',
  secondary: '#8b5cf6',
};

const AnalyticsDashboard = ({ issues = [] }) => {
  const stats = useMemo(() => {
    const total = issues.length;
    const closed = issues.filter(i => i.status === 'Closed' || i.status === 'Resolved').length;
    const open = total - closed;

    const categoryCounts = issues.reduce((acc, issue) => {
      const category = issue.category || 'Uncategorized';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});

    const topCategories = Object.entries(categoryCounts)
      .sort(([, a], [, b]) => b - a)
      .map(([name, count]) => ({ name, count }))
      .slice(0, 10);

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
      closed,
      topCategories,
      topLocations,
      avgResolutionTime,
      pieData: [
        { name: 'Open', value: open, color: COLORS.open },
        { name: 'Closed', value: closed, color: COLORS.closed },
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
        <Card>
          <h3 className="text-lg font-bold text-gray-800 mb-6 border-b border-gray-100 pb-3">Open vs Closed Issues</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.pieData}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {stats.pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-bold text-gray-800 mb-6 border-b border-gray-100 pb-3">Top Categories</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.topCategories} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
              <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#6B7280' }} />
              <YAxis type="category" dataKey="name" width={100} axisLine={false} tickLine={false} tick={{ fill: '#374151', fontSize: 12, fontWeight: 500 }} />
              <Tooltip cursor={{ fill: '#F3F4F6' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} />
              <Bar dataKey="count" fill={COLORS.primary} radius={[0, 4, 4, 0]} barSize={30} />
            </BarChart>
          </ResponsiveContainer>
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
