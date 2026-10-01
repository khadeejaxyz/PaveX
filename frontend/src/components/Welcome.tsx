/**
 * Welcome / Landing Page
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Welcome.css';

const proofPoints = [
    { value: '<200ms', label: 'hazard signal' },
    { value: '15+ FPS', label: 'live inference' },
    { value: '4 levels', label: 'severity routing' },
];

const features = [
    {
        title: 'Detect once',
        body: 'Camera, video, and uploaded images surface potholes, humps, cracks, and debris while the driver keeps moving.',
    },
    {
        title: 'Deduplicate',
        body: 'Repeated sightings fold into one road object with confidence, location, and report count preserved.',
    },
    {
        title: 'Warn approaching drivers',
        body: 'Live alerts translate detections into distance-aware guidance and safer speed recommendations.',
    },
    {
        title: 'Measure the network',
        body: 'Operators can review severity mix, detection volume, confidence, and history from the analytics route.',
    },
];

export default function Welcome() {
    const navigate = useNavigate();
    const [ready, setReady] = useState(false);

    useEffect(() => {
        const t = setTimeout(() => setReady(true), 100);
        return () => clearTimeout(t);
    }, []);

    return (
        <div className={`welcome ${ready ? 'welcome--ready' : ''}`}>
            <header className="welcome__nav">
                <button className="welcome__brand" onClick={() => navigate('/')} type="button">
                    <BrandMark />
                    <span>PaveX</span>
                </button>
                <nav className="welcome__links" aria-label="Landing navigation">
                    <a href="#features">Platform</a>
                    <a href="#signal">Signal Flow</a>
                    <button className="welcome__ghost-btn" onClick={() => navigate('/analytics')} type="button">
                        Analytics
                    </button>
                </nav>
            </header>

            <main className="welcome__hero">
                <div className="welcome__scene" aria-hidden="true">
                    <div className="welcome__map-grid" />
                    <div className="welcome__road welcome__road--main">
                        <span className="welcome__lane" />
                    </div>
                    <div className="welcome__road welcome__road--cross" />
                    <div className="welcome__route welcome__route--one" />
                    <div className="welcome__route welcome__route--two" />
                    <div className="welcome__hazard-pin welcome__hazard-pin--critical">
                        <span />
                    </div>
                    <div className="welcome__hazard-pin welcome__hazard-pin--warning">
                        <span />
                    </div>
                    <div className="welcome__driver">
                        <span />
                    </div>
                    <div className="welcome__signal-card welcome__signal-card--alert">
                        <strong>Critical pothole</strong>
                        <span>180m ahead - slow to 20 km/h</span>
                    </div>
                    <div className="welcome__signal-card welcome__signal-card--feed">
                        <strong>3 reports merged</strong>
                        <span>Confidence rising: 91%</span>
                    </div>
                </div>

                <section className="welcome__hero-copy">
                    <p className="welcome__eyebrow">Road intelligence from one detected hazard</p>
                    <h1>PaveX</h1>
                    <p className="welcome__lede">
                        A polished safety command layer that turns live road-hazard detection into
                        shared warnings, map context, and speed guidance for drivers and operators.
                    </p>
                    <div className="welcome__actions">
                        <button className="welcome__primary-btn" onClick={() => navigate('/dashboard')} type="button">
                            <PlayIcon />
                            Open Dashboard
                        </button>
                        <button className="welcome__secondary-btn" onClick={() => navigate('/settings')} type="button">
                            Tune Alerts
                        </button>
                    </div>
                    <div className="welcome__proof">
                        {proofPoints.map((point) => (
                            <div className="welcome__proof-item" key={point.label}>
                                <strong>{point.value}</strong>
                                <span>{point.label}</span>
                            </div>
                        ))}
                    </div>
                </section>
            </main>

            <section id="features" className="welcome__features">
                {features.map((feature, index) => (
                    <article
                        className="welcome__feature"
                        key={feature.title}
                        style={{ animationDelay: `${index * 0.08}s` }}
                    >
                        <span className="welcome__feature-step">0{index + 1}</span>
                        <h2>{feature.title}</h2>
                        <p>{feature.body}</p>
                    </article>
                ))}
            </section>

            <section id="signal" className="welcome__signal">
                <div>
                    <p className="welcome__eyebrow">Live driver loop</p>
                    <h2>Camera to cockpit in one continuous flow.</h2>
                </div>
                <div className="welcome__signal-rail" aria-label="PaveX signal flow">
                    {['Capture', 'Classify', 'Merge', 'Warn', 'Analyze'].map((step) => (
                        <span key={step}>{step}</span>
                    ))}
                </div>
            </section>
        </div>
    );
}

function BrandMark() {
    return (
        <svg className="welcome__brand-icon" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="7" fill="#102023" />
            <path d="M7 22h18" stroke="#F6C453" strokeWidth="2.4" strokeLinecap="round" />
            <path d="M10 21l4-11 4 11" stroke="#F8FAFC" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M19 13l4 8" stroke="#54B8A9" strokeWidth="2.4" strokeLinecap="round" />
        </svg>
    );
}

function PlayIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M8 5v14l11-7L8 5z" fill="currentColor" />
        </svg>
    );
}
