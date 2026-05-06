/**
 * AlertFeed Component
 * Displays real-time alerts with acknowledgement
 */

import { useEffect, useRef } from 'react';
import { useReducedMotion } from '../hooks';
import type { AlertFeedProps, Alert } from '../types';
import './AlertFeed.css';

export default function AlertFeed({
    alerts,
    onAcknowledge,
    className = '',
}: AlertFeedProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const prefersReducedMotion = useReducedMotion();

    // Auto-scroll to newest alert
    useEffect(() => {
        if (containerRef.current && !prefersReducedMotion) {
            containerRef.current.scrollTo({
                top: 0,
                behavior: 'smooth',
            });
        }
    }, [alerts.length, prefersReducedMotion]);

    const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged);

    return (
        <div className={`alert-feed ${className}`}>
            <div className="alert-feed__header">
                <h3 className="alert-feed__title">Alerts</h3>
                {unacknowledgedAlerts.length > 0 && (
                    <span className="alert-feed__badge">
                        {unacknowledgedAlerts.length}
                    </span>
                )}
            </div>

            <div ref={containerRef} className="alert-feed__list">
                {alerts.length === 0 ? (
                    <div className="alert-feed__empty">
                        <svg className="alert-feed__empty-icon" viewBox="0 0 24 24" fill="none">
                            <path
                                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </svg>
                        <p className="alert-feed__empty-text">No alerts yet</p>
                    </div>
                ) : (
                    alerts.map((alert, index) => (
                        <AlertCard
                            key={alert.id}
                            alert={alert}
                            onAcknowledge={onAcknowledge}
                            index={index}
                        />
                    ))
                )}
            </div>
        </div>
    );
}

interface AlertCardProps {
    alert: Alert;
    onAcknowledge?: (id: string) => void;
    index: number;
}

function AlertCard({ alert, onAcknowledge, index }: AlertCardProps) {
    const prefersReducedMotion = useReducedMotion();

    return (
        <div
            className={`alert-card alert-card--${alert.severity} ${alert.acknowledged ? 'alert-card--acknowledged' : ''
                }`}
            style={
                !prefersReducedMotion
                    ? {
                        animationDelay: `${index * 0.05}s`,
                    }
                    : undefined
            }
        >
            <div className="alert-card__icon">
                {getAlertIcon(alert.severity)}
            </div>

            <div className="alert-card__content">
                <div className="alert-card__header">
                    <h4 className="alert-card__title">
                        {formatHazardType(alert.hazardType)}
                    </h4>
                    <span className={`alert-card__badge alert-card__badge--${alert.severity}`}>
                        {alert.severity}
                    </span>
                </div>

                <p className="alert-card__message">{alert.message}</p>

                <div className="alert-card__meta">
                    {alert.distance !== undefined && (
                        <span className="alert-card__distance">
                            <svg viewBox="0 0 24 24" fill="none">
                                <path
                                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                                <path
                                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </svg>
                            {Math.round(alert.distance)}m ahead
                        </span>
                    )}
                    <span className="alert-card__time">
                        {formatTimeAgo(alert.timestamp)}
                    </span>
                </div>
            </div>

            {!alert.acknowledged && onAcknowledge && (
                <button
                    className="alert-card__action"
                    onClick={() => onAcknowledge(alert.id)}
                    aria-label="Acknowledge alert"
                >
                    <svg viewBox="0 0 24 24" fill="none">
                        <path
                            d="M5 13l4 4L19 7"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                </button>
            )}
        </div>
    );
}

/**
 * Get icon for alert severity
 */
function getAlertIcon(severity: string) {
    if (severity === 'critical' || severity === 'high') {
        return (
            <svg viewBox="0 0 24 24" fill="none">
                <path
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </svg>
        );
    }

    return (
        <svg viewBox="0 0 24 24" fill="none">
            <path
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

/**
 * Format hazard type for display
 */
function formatHazardType(type: string): string {
    return type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Format timestamp as time ago
 */
function formatTimeAgo(timestamp: string): string {
    const now = new Date();
    const time = new Date(timestamp);
    const seconds = Math.floor((now.getTime() - time.getTime()) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}