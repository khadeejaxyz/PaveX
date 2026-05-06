/**
 * HazardCard Component
 * Displays individual hazard information
 */

import type { HazardCardProps } from '../types';
import './HazardCard.css';

export default function HazardCard({
    hazard,
    onSelect,
    className = '',
}: HazardCardProps) {
    const isDetection = 'bbox' in hazard;
    const timestamp = isDetection ? hazard.timestamp : hazard.detectedAt;

    return (
        <div
            className={`hazard-card hazard-card--${hazard.severity} ${className}`}
            onClick={onSelect}
            role={onSelect ? 'button' : undefined}
            tabIndex={onSelect ? 0 : undefined}
        >
            <div className="hazard-card__header">
                <div className="hazard-card__icon">
                    {getHazardIcon(hazard.hazardType)}
                </div>
                <div className="hazard-card__title-section">
                    <h4 className="hazard-card__title">
                        {formatHazardType(hazard.hazardType)}
                    </h4>
                    <span className={`hazard-card__badge hazard-card__badge--${hazard.severity}`}>
                        {hazard.severity}
                    </span>
                </div>
            </div>

            <div className="hazard-card__details">
                <div className="hazard-card__detail">
                    <span className="hazard-card__detail-label">Confidence</span>
                    <div className="hazard-card__confidence-bar">
                        <div
                            className="hazard-card__confidence-fill"
                            style={{ width: `${hazard.confidence * 100}%` }}
                        />
                    </div>
                    <span className="hazard-card__detail-value">
                        {Math.round(hazard.confidence * 100)}%
                    </span>
                </div>

                {!isDetection && 'reportCount' in hazard && hazard.reportCount > 1 && (
                    <div className="hazard-card__detail">
                        <span className="hazard-card__detail-label">Reports</span>
                        <span className="hazard-card__detail-value">{hazard.reportCount}</span>
                    </div>
                )}

                <div className="hazard-card__detail">
                    <span className="hazard-card__detail-label">Detected</span>
                    <span className="hazard-card__detail-value">
                        {formatTimeAgo(timestamp)}
                    </span>
                </div>
            </div>

            {!isDetection && 'verified' in hazard && hazard.verified && (
                <div className="hazard-card__verified">
                    <svg viewBox="0 0 24 24" fill="none">
                        <path
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                    <span>Verified</span>
                </div>
            )}
        </div>
    );
}

/**
 * Get icon for hazard type
 */
function getHazardIcon(type: string) {
    const icons: Record<string, JSX.Element> = {
        pothole: (
            <svg viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="4" />
            </svg>
        ),
        speed_hump: (
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M2 12h20M6 8l6-4 6 4" stroke="currentColor" strokeWidth="2" fill="none" />
            </svg>
        ),
        crack: (
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
        ),
        debris: (
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
        ),
        other: (
            <svg viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10" />
            </svg>
        ),
    };

    return icons[type] || icons.other;
}

/**
 * Format hazard type for display
 */
function formatHazardType(type: string): string {
    return type
        .split('_')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
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