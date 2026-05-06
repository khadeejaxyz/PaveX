/**
 * Analytics & History Page
 * Charts and history view matching Stitch screen #4
 */

import { useEffect, useState } from 'react';
import {
    AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useStore } from '../store/useStore';
import { api } from '../services/api';
import './Analytics.css';

const SEVERITY_COLORS: Record<string, string> = {
    low: '#22C55E',
    medium: '#F59E0B',
    high: '#EF4444',
    critical: '#B91C1C',
};

const HAZARD_COLORS = [
    '#3B5998', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6'
];

export default function Analytics() {
    const statistics = useStore((state) => state.statistics);
    const setStatistics = useStore((state) => state.setStatistics);
    const detectionHistory = useStore((state) => state.detectionHistory);
    const [loading, setLoading] = useState(false);
    const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

    useEffect(() => {
        setLoading(true);
        api.getStatistics().then((stats) => {
            if (stats) setStatistics(stats);
            setLoading(false);
        });
    }, [setStatistics]);

    // Build hourly chart data
    const hourlyData = (statistics?.detectionsByHour || Array(24).fill(0)).map(
        (count, hour) => ({
            hour: `${hour.toString().padStart(2, '0')}:00`,
            detections: count,
        })
    );

    // Build severity pie data
    const severityData = statistics
        ? Object.entries(statistics.severityDistribution).map(([name, value]) => ({
            name: name.charAt(0).toUpperCase() + name.slice(1),
            value,
            color: SEVERITY_COLORS[name],
        }))
        : [];

    // Build hazard type bar data
    const hazardTypeData = statistics
        ? Object.entries(statistics.hazardTypeDistribution).map(([name, value]) => ({
            name: name.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
            count: value,
        }))
        : [];

    return (
        <div className="analytics">
            {/* Header */}
            <div className="analytics__header">
                <div>
                    <h2 className="analytics__title">Analytics & History</h2>
                    <p className="analytics__subtitle">Detection trends and hazard statistics</p>
                </div>
                <div className="analytics__time-range">
                    {(['24h', '7d', '30d'] as const).map((range) => (
                        <button
                            key={range}
                            className={`analytics__range-btn ${timeRange === range ? 'active' : ''}`}
                            onClick={() => setTimeRange(range)}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="analytics__loading">
                    <div className="analytics__spinner" />
                    <p>Loading analytics...</p>
                </div>
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="analytics__kpis">
                        <KPICard
                            label="Total Detections"
                            value={statistics?.totalDetections ?? 0}
                            icon="🔍"
                            color="primary"
                        />
                        <KPICard
                            label="Today"
                            value={statistics?.todayDetections ?? 0}
                            icon="📅"
                            color="success"
                        />
                        <KPICard
                            label="Avg Confidence"
                            value={`${Math.round((statistics?.averageConfidence ?? 0) * 100)}%`}
                            icon="🎯"
                            color="warning"
                        />
                        <KPICard
                            label="Critical Hazards"
                            value={statistics?.severityDistribution?.critical ?? 0}
                            icon="🚨"
                            color="danger"
                        />
                    </div>

                    {/* Charts Grid */}
                    <div className="analytics__charts">
                        {/* Detections Over Time */}
                        <div className="analytics__chart-card analytics__chart-card--wide">
                            <h3 className="analytics__chart-title">Detections Over Time</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <AreaChart data={hourlyData}>
                                    <defs>
                                        <linearGradient id="detectionsGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3B5998" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3B5998" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                                    <XAxis
                                        dataKey="hour"
                                        tick={{ fontSize: 11, fill: '#64748B' }}
                                        tickLine={false}
                                        axisLine={false}
                                        interval={3}
                                    />
                                    <YAxis
                                        tick={{ fontSize: 11, fill: '#64748B' }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            background: '#FFFFFF',
                                            border: '1px solid #E2E8F0',
                                            borderRadius: '8px',
                                            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                                        }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="detections"
                                        stroke="#3B5998"
                                        strokeWidth={2}
                                        fill="url(#detectionsGradient)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Severity Distribution */}
                        <div className="analytics__chart-card">
                            <h3 className="analytics__chart-title">By Severity</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <PieChart>
                                    <Pie
                                        data={severityData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={90}
                                        paddingAngle={3}
                                        dataKey="value"
                                    >
                                        {severityData.map((entry, index) => (
                                            <Cell key={index} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{
                                            background: '#FFFFFF',
                                            border: '1px solid #E2E8F0',
                                            borderRadius: '8px',
                                        }}
                                    />
                                    <Legend
                                        iconType="circle"
                                        iconSize={10}
                                        formatter={(value) => (
                                            <span style={{ fontSize: '12px', color: '#475569' }}>{value}</span>
                                        )}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Hazard Types */}
                        <div className="analytics__chart-card">
                            <h3 className="analytics__chart-title">By Hazard Type</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={hazardTypeData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                                    <XAxis
                                        type="number"
                                        tick={{ fontSize: 11, fill: '#64748B' }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        type="category"
                                        dataKey="name"
                                        tick={{ fontSize: 11, fill: '#64748B' }}
                                        tickLine={false}
                                        axisLine={false}
                                        width={90}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            background: '#FFFFFF',
                                            border: '1px solid #E2E8F0',
                                            borderRadius: '8px',
                                        }}
                                    />
                                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                                        {hazardTypeData.map((_, index) => (
                                            <Cell key={index} fill={HAZARD_COLORS[index % HAZARD_COLORS.length]} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Recent History Table */}
                    <div className="analytics__history">
                        <h3 className="analytics__chart-title">Detection History</h3>
                        <div className="analytics__table-wrapper">
                            <table className="analytics__table">
                                <thead>
                                    <tr>
                                        <th>Type</th>
                                        <th>Severity</th>
                                        <th>Confidence</th>
                                        <th>Time</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {detectionHistory.slice(0, 20).map((d) => (
                                        <tr key={d.id}>
                                            <td className="analytics__td-type">
                                                {d.hazardType.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                                            </td>
                                            <td>
                                                <span className={`analytics__severity analytics__severity--${d.severity}`}>
                                                    {d.severity}
                                                </span>
                                            </td>
                                            <td className="analytics__td-mono">
                                                {Math.round(d.confidence * 100)}%
                                            </td>
                                            <td className="analytics__td-time">
                                                {new Date(d.timestamp).toLocaleTimeString()}
                                            </td>
                                        </tr>
                                    ))}
                                    {detectionHistory.length === 0 && (
                                        <tr>
                                            <td colSpan={4} className="analytics__table-empty">
                                                No detection history yet
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

/* KPI Card sub-component */
interface KPICardProps {
    label: string;
    value: string | number;
    icon: string;
    color: 'primary' | 'success' | 'warning' | 'danger';
}

function KPICard({ label, value, icon, color }: KPICardProps) {
    return (
        <div className={`kpi-card kpi-card--${color}`}>
            <div className="kpi-card__icon">{icon}</div>
            <div className="kpi-card__body">
                <span className="kpi-card__label">{label}</span>
                <span className="kpi-card__value">{value}</span>
            </div>
        </div>
    );
}
