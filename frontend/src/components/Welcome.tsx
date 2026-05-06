/**
 * Welcome / Landing Page
 * PaveX brand splash — Stitch screen #1
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Welcome.css';

export default function Welcome() {
    const navigate = useNavigate();
    const [ready, setReady] = useState(false);

    useEffect(() => {
        // Small delay so all fonts / assets settle before animating
        const t = setTimeout(() => setReady(true), 100);
        return () => clearTimeout(t);
    }, []);

    return (
        <div className={`welcome ${ready ? 'welcome--ready' : ''}`}>
            {/* Ambient background orbs */}
            <div className="welcome__orb welcome__orb--1" />
            <div className="welcome__orb welcome__orb--2" />
            <div className="welcome__orb welcome__orb--3" />

            {/* Top nav bar */}
            <header className="welcome__nav">
                <div className="welcome__brand">
                    <svg className="welcome__brand-icon" viewBox="0 0 32 32" fill="none">
                        <rect width="32" height="32" rx="8" fill="var(--color-primary-600)" />
                        <path
                            d="M8 22l4-8 4 6 3-4 5 6"
                            stroke="white"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                    <span className="welcome__brand-name">PaveX</span>
                </div>
                <nav className="welcome__links">
                    <a href="#features" className="welcome__link">Features</a>
                    <a href="#about" className="welcome__link">About</a>
                    <button
                        className="welcome__btn welcome__btn--outline"
                        onClick={() => navigate('/dashboard')}
                    >
                        Open App
                    </button>
                </nav>
            </header>

            {/* Hero */}
            <main className="welcome__hero">
                <div className="welcome__hero-content">
                    <div className="welcome__badge">
                        <span className="welcome__badge-dot" />
                        AI-Powered Road Safety
                    </div>

                    <h1 className="welcome__headline">
                        <span className="welcome__word">Smart</span>{' '}
                        <span className="welcome__word">Road</span>{' '}
                        <span className="welcome__word welcome__word--accent">Hazard</span>{' '}
                        <span className="welcome__word">Detection</span>
                    </h1>

                    <p className="welcome__description">
                        PaveX uses real-time YOLOv8 computer vision to detect potholes, speed humps,
                        and road hazards — providing instant alerts and speed recommendations to keep
                        drivers safe.
                    </p>

                    <div className="welcome__actions">
                        <button
                            className="welcome__btn welcome__btn--primary"
                            onClick={() => navigate('/dashboard')}
                        >
                            <svg viewBox="0 0 24 24" fill="none">
                                <path d="M5 3l14 9-14 9V3z" fill="currentColor" />
                            </svg>
                            Launch Dashboard
                        </button>
                        <button
                            className="welcome__btn welcome__btn--secondary"
                            onClick={() => navigate('/analytics')}
                        >
                            View Analytics
                        </button>
                    </div>

                    {/* Quick stats */}
                    <div className="welcome__stats">
                        {[
                            { value: '<200ms', label: 'Detection Latency' },
                            { value: '>85%', label: 'Accuracy' },
                            { value: '15+ FPS', label: 'Live Inference' },
                            { value: '4', label: 'Severity Levels' },
                        ].map((s) => (
                            <div key={s.label} className="welcome__stat">
                                <span className="welcome__stat-value">{s.value}</span>
                                <span className="welcome__stat-label">{s.label}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Illustration panel */}
                <div className="welcome__illustration">
                    <div className="welcome__screen-mock">
                        <div className="welcome__screen-bar">
                            <span /><span /><span />
                        </div>
                        <div className="welcome__screen-body">
                            <div className="welcome__mock-feed">
                                <div className="welcome__mock-bbox welcome__mock-bbox--high" />
                                <div className="welcome__mock-bbox welcome__mock-bbox--medium" />
                            </div>
                            <div className="welcome__mock-sidebar">
                                <div className="welcome__mock-line" />
                                <div className="welcome__mock-line welcome__mock-line--short" />
                                <div className="welcome__mock-badge welcome__mock-badge--danger" />
                                <div className="welcome__mock-line" />
                                <div className="welcome__mock-line welcome__mock-line--short" />
                                <div className="welcome__mock-badge welcome__mock-badge--warn" />
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            {/* Feature Cards */}
            <section id="features" className="welcome__features">
                {[
                    {
                        icon: '🎯',
                        title: 'Real-Time Detection',
                        body: 'YOLOv8 model processes live video frames at 15+ FPS to instantly identify potholes, humps, cracks, and debris.',
                    },
                    {
                        icon: '🗺️',
                        title: 'Geo-Mapped Hazards',
                        body: 'Every detection is GPS-tagged and plotted on an interactive map so you always know what lies ahead.',
                    },
                    {
                        icon: '🔔',
                        title: 'Smart Alerts',
                        body: 'WebSocket-powered alerts with configurable severity thresholds and proximity distance filtering.',
                    },
                    {
                        icon: '📊',
                        title: 'Analytics Dashboard',
                        body: 'Charts, detection history, severity trends and confidence scores — all in one unified view.',
                    },
                ].map((f, i) => (
                    <div
                        key={f.title}
                        className="welcome__feature-card"
                        style={{ animationDelay: `${0.1 + i * 0.08}s` }}
                    >
                        <div className="welcome__feature-icon">{f.icon}</div>
                        <h3 className="welcome__feature-title">{f.title}</h3>
                        <p className="welcome__feature-body">{f.body}</p>
                    </div>
                ))}
            </section>

            <footer className="welcome__footer">
                <p>© 2026 PaveX — Smart Road Hazard Monitor</p>
            </footer>
        </div>
    );
}