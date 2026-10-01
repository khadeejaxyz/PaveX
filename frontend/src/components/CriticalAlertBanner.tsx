import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import './CriticalAlertBanner.css';

const AUTO_DISMISS_SECONDS = 8;

export const CriticalAlertBanner: React.FC = () => {
    const alerts = useStore((state) => state.alerts);
    const acknowledgeAlert = useStore((state) => state.acknowledgeAlert);

    // Find the newest unacknowledged alert with severity 'critical' or 'high'
    const activeAlert = alerts.find(
        (a) => !a.acknowledged && (a.severity === 'critical' || a.severity === 'high')
    );

    const [progress, setProgress] = useState(100);

    useEffect(() => {
        if (!activeAlert) {
            setProgress(100);
            return;
        }

        const alertId = activeAlert.id;
        const startTime = Date.now();
        const duration = AUTO_DISMISS_SECONDS * 1000;

        const interval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const remainingRatio = Math.max(0, 1 - elapsed / duration);
            setProgress(remainingRatio * 100);

            if (elapsed >= duration) {
                acknowledgeAlert(alertId);
                clearInterval(interval);
            }
        }, 100);

        return () => clearInterval(interval);
    }, [activeAlert?.id, acknowledgeAlert]);

    if (!activeAlert) {
        return null;
    }

    const isCritical = activeAlert.severity === 'critical';
    const recommendedSpeed = activeAlert.recommendedSpeedKmph;
    const formattedHazard = (activeAlert.hazardType || 'Hazard').replace(/_/g, ' ');

    const handleDismiss = () => {
        acknowledgeAlert(activeAlert.id);
    };

    return (
        <aside
            className={`critical-alert-banner ${isCritical ? 'critical-alert-banner--critical' : 'critical-alert-banner--high'}`}
            role="alert"
            aria-live="assertive"
        >
            <div className="critical-alert-banner__glow" aria-hidden="true" />

            <div className="critical-alert-banner__container">
                {/* Warning Icon & Pulse */}
                <div className="critical-alert-banner__icon-wrap">
                    <span className="critical-alert-banner__pulse" />
                    <svg
                        className="critical-alert-banner__icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                </div>

                {/* Content */}
                <div className="critical-alert-banner__content">
                    <div className="critical-alert-banner__header">
                        <span className="critical-alert-banner__badge">
                            {isCritical ? 'CRITICAL ALERT' : 'HIGH PRIORITY WARNING'}
                        </span>
                        {activeAlert.distance !== undefined && (
                            <span className="critical-alert-banner__distance">
                                {Math.round(activeAlert.distance)}m AHEAD
                            </span>
                        )}
                    </div>

                    <h2 className="critical-alert-banner__title">
                        {formattedHazard.toUpperCase()}
                    </h2>

                    <p className="critical-alert-banner__message">
                        {activeAlert.message || `Imminent road hazard detected ahead. Reduce speed immediately.`}
                    </p>
                </div>

                {/* Recommended Speed Badge */}
                {recommendedSpeed !== undefined && recommendedSpeed !== null && (
                    <div className="critical-alert-banner__speed">
                        <span className="critical-alert-banner__speed-label">REDUCE TO</span>
                        <div className="critical-alert-banner__speed-dial">
                            <span className="critical-alert-banner__speed-value">{Math.round(recommendedSpeed)}</span>
                            <span className="critical-alert-banner__speed-unit">KM/H</span>
                        </div>
                    </div>
                )}

                {/* Dismiss Button */}
                <button
                    type="button"
                    className="critical-alert-banner__dismiss"
                    onClick={handleDismiss}
                    aria-label="Dismiss alert"
                >
                    <span className="critical-alert-banner__dismiss-text">DISMISS</span>
                    <svg
                        className="critical-alert-banner__dismiss-icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                </button>
            </div>

            {/* Timeout Progress Bar */}
            <div className="critical-alert-banner__progress-bar">
                <div
                    className="critical-alert-banner__progress-fill"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </aside>
    );
};

export default CriticalAlertBanner;
