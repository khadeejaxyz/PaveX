/**
 * Dashboard — Unified Multi-Source Input (Stitch screen #3)
 */

import { useEffect, useRef, useState } from 'react';
import { useStore } from '../store/useStore';
import { api } from '../services/api';
import { useDetection } from '../hooks';
import LiveFeed from './LiveFeed';
import MapPanel from './MapPanel';
import AlertFeed from './AlertFeed';
import SpeedMeter from './SpeedMeter';
import HazardCard from './HazardCard';
import type { InputSource } from '../types';
import './Dashboard.css';

export default function Dashboard() {
    const currentDetections = useStore((s) => s.currentDetections);
    const alerts = useStore((s) => s.alerts);
    const nearbyHazards = useStore((s) => s.nearbyHazards);
    const currentLocation = useStore((s) => s.currentLocation);
    const selectedHazard = useStore((s) => s.selectedHazard);
    const systemStatus = useStore((s) => s.systemStatus);
    const statistics = useStore((s) => s.statistics);
    const inputSource = useStore((s) => s.inputSource);

    const setNearbyHazards = useStore((s) => s.setNearbyHazards);
    const acknowledgeAlert = useStore((s) => s.acknowledgeAlert);
    const selectHazard = useStore((s) => s.selectHazard);
    const setInputSource = useStore((s) => s.setInputSource);
    const clearDetections = useStore((s) => s.clearDetections);

    const { detectImage } = useDetection();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const videoInputRef = useRef<HTMLInputElement>(null);
    const [dragging, setDragging] = useState(false);
    const [imagePreview, setPreview] = useState<string | null>(null);
    const [videoPreview, setVideoPreview] = useState<string | null>(null);

    // Load all hazards on mount so hazards show before WebSocket delivers anything
    useEffect(() => {
        api.getAllHazards().then((hazards) => {
            if (hazards && hazards.length > 0) {
                setNearbyHazards(hazards);
            }
        });
    }, [setNearbyHazards]);

    // FIX: Keep hazards fresh via polling — MERGE with the existing list
    // instead of replacing it. getNearbyHazards() is radius-filtered by
    // currentLocation, so if GPS drifts or a hazard sits just outside the
    // radius, a flat setNearbyHazards(nearby) would silently delete markers
    // that were already correctly showing on the map ("hazards show on
    // refresh but don't persist"). Merging by id means the poll can only
    // add/update hazards, never remove ones we already know about.
    useEffect(() => {
        if (!currentLocation) return;

        const refresh = () => {
            api
                .getNearbyHazards(currentLocation.latitude, currentLocation.longitude, 1000)
                .then((nearby) => {
                    useStore.setState((state) => {
                        const merged = new Map(state.nearbyHazards.map((h) => [h.id, h]));
                        nearby.forEach((h) => merged.set(h.id, h));
                        return { nearbyHazards: Array.from(merged.values()) };
                    });
                });
        };

        refresh(); // immediate fetch on location lock/change
        const interval = setInterval(refresh, 5000); // poll every 5s

        return () => clearInterval(interval);
    }, [currentLocation]);

    // FIX: Speed recommendation now comes from the backend's actual decision
    // engine (recommendedSpeedKmph on each hazard) instead of a hardcoded
    // 20/40 guess, and currentSpeed reads real GPS speed instead of a
    // permanently frozen 45.
    const hazardsWithSpeed = nearbyHazards.filter(
        (h) => h.recommendedSpeedKmph !== undefined && h.recommendedSpeedKmph !== null
    );
    const maxSafeSpeed = 50;
    const recommendedSpeed = hazardsWithSpeed.length > 0
        ? Math.min(...hazardsWithSpeed.map((h) => h.recommendedSpeedKmph as number))
        : maxSafeSpeed;
    const hasCritical = nearbyHazards.some(
        (h) => h.severity === 'critical' || h.severity === 'high'
    );
    const currentSpeed = currentLocation?.speedKmph ?? 0;

    // File / drag handlers
    async function handleFile(file: File) {
        const url = URL.createObjectURL(file);
        setPreview(url);
        setVideoPreview(null);
        clearDetections();
        setInputSource('image');
        try { await detectImage(file); } catch { }
    }

    function handleVideoFile(file: File) {
        const url = URL.createObjectURL(file);
        setVideoPreview(url);
        setPreview(null);
        clearDetections();
        setInputSource('video');
    }

    function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
        e.target.value = '';
    }

    function onVideoChange(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (file) handleVideoFile(file);
        e.target.value = '';
    }

    function onDrop(e: React.DragEvent) {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (!file) return;

        if (file.type.startsWith('video/')) {
            handleVideoFile(file);
        } else {
            handleFile(file);
        }
    }

    function handleSourceClick(src: InputSource) {
        if (src !== inputSource) {
            clearDetections();
        }

        setInputSource(src);

        if (src === 'camera') {
            setPreview(null);
            setVideoPreview(null);
        }

        if (src === 'video') {
            videoInputRef.current?.click();
        }
    }

    return (
        <div className="dashboard">
            <header className="dashboard__hero">
                <div>
                    <p className="dashboard__eyebrow">Driver Command Center</p>
                    <h1>Live road intelligence</h1>
                    <p>
                        One hazard detection becomes shared location context, alert priority, and
                        immediate speed guidance.
                    </p>
                </div>
                <div className="dashboard__mission">
                    <span>Recommended</span>
                    <strong>{recommendedSpeed} km/h</strong>
                    <small>{hasCritical ? 'High severity active' : 'Route within safe envelope'}</small>
                </div>
            </header>

            {/* ── Top status bar ── */}
            <div className="dashboard__statusbar">
                <StatusChip label="Camera" ok={systemStatus.camera === 'connected'} />
                <StatusChip label="Detection" ok={systemStatus.detection === 'active'} />
                <StatusChip label="WebSocket" ok={systemStatus.websocket === 'connected'} />
                <StatusChip label="GPS" ok={systemStatus.gps === 'available'} />
                <div className="dashboard__fps">
                    <span>FPS</span>
                    <strong>{systemStatus.fps}</strong>
                </div>
                {statistics && (
                    <>
                        <div className="dashboard__kpi">
                            <span>Total</span>
                            <strong>{statistics.totalDetections}</strong>
                        </div>
                        <div className="dashboard__kpi">
                            <span>Today</span>
                            <strong>{statistics.todayDetections}</strong>
                        </div>
                    </>
                )}
            </div>

            {/* ── Source selector ── */}
            <div className="dashboard__source-bar">
                {(['camera', 'video', 'image'] as InputSource[]).map((src) => (
                    <button
                        key={src}
                        className={`dashboard__src-btn ${inputSource === src ? 'dashboard__src-btn--active' : ''}`}
                        onClick={() => handleSourceClick(src)}
                        type="button"
                    >
                        <SourceIcon source={src} />
                        <span>{src.charAt(0).toUpperCase() + src.slice(1)}</span>
                    </button>
                ))}

                {/* Image upload drop zone */}
                {inputSource === 'image' && (
                    <div
                        className={`dashboard__dropzone ${dragging ? 'dashboard__dropzone--drag' : ''}`}
                        onClick={() => fileInputRef.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={onDrop}
                        role="button"
                        tabIndex={0}
                        aria-label="Upload image for detection"
                    >
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 20M14 8h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span>Drop image or click to upload</span>
                    </div>
                )}
                {inputSource === 'video' && (
                    <div
                        className={`dashboard__dropzone ${dragging ? 'dashboard__dropzone--drag' : ''}`}
                        onClick={() => videoInputRef.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={onDrop}
                        role="button"
                        tabIndex={0}
                        aria-label="Upload video for detection"
                    >
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span>{videoPreview ? 'Change video' : 'Choose video for detection'}</span>
                    </div>
                )}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="sr-only"
                    onChange={onFileChange}
                    aria-label="Image file input"
                />
                <input
                    ref={videoInputRef}
                    type="file"
                    accept="video/*"
                    className="sr-only"
                    onChange={onVideoChange}
                    aria-label="Video file input"
                />
            </div>

            {/* ── Main grid ── */}
            <div className="dashboard__grid">

                {/* LEFT — Live feed / image preview */}
                <section className="dashboard__live">
                    {inputSource === 'image' && imagePreview ? (
                        <div className="dashboard__image-preview">
                            <img src={imagePreview} alt="Uploaded for detection" />
                            <button
                                className="dashboard__image-clear"
                                onClick={() => { setPreview(null); setInputSource('camera'); }}
                                aria-label="Clear image"
                            >✕</button>
                        </div>
                    ) : (
                        <LiveFeed videoSrc={inputSource === 'video' ? videoPreview : null} />
                    )}
                </section>

                {/* CENTER — Map + speed */}
                <section className="dashboard__center">
                    <div className="dashboard__map">
                        <MapPanel
                            hazards={nearbyHazards}
                            currentLocation={currentLocation ?? undefined}
                            selectedHazard={selectedHazard}
                            onHazardSelect={selectHazard}
                        />
                    </div>
                    <div className="dashboard__speed">
                        <SpeedMeter
                            current={currentSpeed}
                            recommended={recommendedSpeed}
                            maxSafe={maxSafeSpeed}
                            unit="kmh"
                        />
                    </div>
                </section>

                {/* RIGHT — Alerts + recent detections */}
                <section className="dashboard__sidebar">
                    <div className="dashboard__alerts">
                        <AlertFeed alerts={alerts} onAcknowledge={acknowledgeAlert} />
                    </div>

                    <div className="dashboard__recent">
                        <h3 className="dashboard__recent-title">Recent Detections</h3>
                        <div className="dashboard__recent-list">
                            {currentDetections.length === 0 ? (
                                <p className="dashboard__recent-empty">No detections yet</p>
                            ) : (
                                currentDetections.slice(0, 6).map((d) => (
                                    <HazardCard key={d.id} hazard={d} />
                                ))
                            )}
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}

/* Small status chip */
function StatusChip({ label, ok }: { label: string; ok: boolean }) {
    return (
        <div className={`status-chip ${ok ? 'status-chip--ok' : 'status-chip--err'}`}>
            <span className="status-chip__dot" />
            {label}
        </div>
    );
}

function SourceIcon({ source }: { source: InputSource }) {
    if (source === 'camera') {
        return (
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M5 7h3l1.5-2h5L16 7h3a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
                <circle cx="12" cy="13" r="3.5" stroke="currentColor" strokeWidth="2" />
            </svg>
        );
    }

    if (source === 'video') {
        return (
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M5 7h9a2 2 0 012 2v1.5l4-2.5v8l-4-2.5V15a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
            </svg>
        );
    }

    return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M5 5h14v14H5z" stroke="currentColor" strokeWidth="2" />
            <path d="M7 16l3.5-4 3 3 2-2 2.5 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="15.5" cy="8.5" r="1.5" fill="currentColor" />
        </svg>
    );
}