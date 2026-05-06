/**
 * SpeedMeter Component
 * Displays current speed with recommendations
 */

import { useEffect, useState } from 'react';
import type { SpeedMeterProps } from '../types';
import './SpeedMeter.css';

export default function SpeedMeter({
    current,
    recommended,
    maxSafe,
    unit = 'kmh',
    className = '',
}: SpeedMeterProps) {
    const [displaySpeed, setDisplaySpeed] = useState(0);

    // Animate speed changes
    useEffect(() => {
        const duration = 300;
        const steps = 20;
        const stepDuration = duration / steps;
        const increment = (current - displaySpeed) / steps;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            setDisplaySpeed((prev) => {
                if (step >= steps) {
                    clearInterval(timer);
                    return current;
                }
                return prev + increment;
            });
        }, stepDuration);

        return () => clearInterval(timer);
    }, [current]);

    const speedPercentage = (displaySpeed / maxSafe) * 100;
    const isSpeeding = displaySpeed > recommended;
    const isUnsafe = displaySpeed > maxSafe;

    return (
        <div className={`speed-meter ${className}`}>
            <div className="speed-meter__gauge">
                {/* Background arc */}
                <svg className="speed-meter__svg" viewBox="0 0 200 120">
                    {/* Safe zone */}
                    <path
                        d="M 20 100 A 80 80 0 0 1 100 20"
                        fill="none"
                        stroke="var(--color-success-200)"
                        strokeWidth="12"
                        strokeLinecap="round"
                    />
                    {/* Caution zone */}
                    <path
                        d="M 100 20 A 80 80 0 0 1 180 100"
                        fill="none"
                        stroke="var(--color-warning-200)"
                        strokeWidth="12"
                        strokeLinecap="round"
                    />

                    {/* Current speed indicator */}
                    <path
                        d={`M 20 100 A 80 80 0 ${speedPercentage > 50 ? '1' : '0'} 1 ${20 + Math.cos((speedPercentage / 100) * Math.PI - Math.PI) * 80
                            } ${100 - Math.sin((speedPercentage / 100) * Math.PI - Math.PI) * 80}`}
                        fill="none"
                        stroke={isUnsafe ? 'var(--color-danger-500)' : isSpeeding ? 'var(--color-warning-500)' : 'var(--color-success-500)'}
                        strokeWidth="12"
                        strokeLinecap="round"
                        className="speed-meter__progress"
                    />

                    {/* Needle */}
                    <line
                        x1="100"
                        y1="100"
                        x2={100 + Math.cos((speedPercentage / 100) * Math.PI - Math.PI) * 70}
                        y2={100 - Math.sin((speedPercentage / 100) * Math.PI - Math.PI) * 70}
                        stroke={isUnsafe ? 'var(--color-danger-600)' : isSpeeding ? 'var(--color-warning-600)' : 'var(--color-success-600)'}
                        strokeWidth="3"
                        strokeLinecap="round"
                        className="speed-meter__needle"
                    />

                    {/* Center dot */}
                    <circle
                        cx="100"
                        cy="100"
                        r="6"
                        fill={isUnsafe ? 'var(--color-danger-600)' : isSpeeding ? 'var(--color-warning-600)' : 'var(--color-success-600)'}
                    />
                </svg>

                {/* Speed display */}
                <div className="speed-meter__display">
                    <div className="speed-meter__value">
                        {Math.round(displaySpeed)}
                    </div>
                    <div className="speed-meter__unit">{unit}</div>
                </div>
            </div>

            {/* Recommendations */}
            <div className="speed-meter__info">
                <div className="speed-meter__info-item">
                    <span className="speed-meter__info-label">Recommended</span>
                    <span className="speed-meter__info-value">
                        {Math.round(recommended)} {unit}
                    </span>
                </div>
                <div className="speed-meter__info-item">
                    <span className="speed-meter__info-label">Max Safe</span>
                    <span className="speed-meter__info-value">
                        {Math.round(maxSafe)} {unit}
                    </span>
                </div>
            </div>

            {/* Warning */}
            {isSpeeding && (
                <div className={`speed-meter__warning ${isUnsafe ? 'speed-meter__warning--danger' : ''}`}>
                    <svg viewBox="0 0 24 24" fill="none">
                        <path
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                    <span>
                        {isUnsafe ? 'UNSAFE SPEED!' : 'Slow down'}
                    </span>
                </div>
            )}
        </div>
    );
}