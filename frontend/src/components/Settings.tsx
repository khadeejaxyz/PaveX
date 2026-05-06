/**
 * Settings & System Status Page
 * Matches Stitch screen #5
 */

import { useState } from 'react';
import { useStore } from '../store/useStore';
import type { SeverityLevel } from '../types';
import './Settings.css';

export default function Settings() {
    const settings = useStore((state) => state.settings);
    const updateSettings = useStore((state) => state.updateSettings);
    const systemStatus = useStore((state) => state.systemStatus);
    const [saved, setSaved] = useState(false);

    function handleToggle(key: keyof typeof settings) {
        updateSettings({ [key]: !settings[key as keyof typeof settings] });
        flashSaved();
    }

    function handleChange<K extends keyof typeof settings>(
        key: K,
        value: typeof settings[K]
    ) {
        updateSettings({ [key]: value });
        flashSaved();
    }

    function flashSaved() {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    }

    const systemHealth = [
        {
            label: 'Camera Feed',
            status: systemStatus.camera,
            icon: '📷',
            description: 'Live video input source',
        },
        {
            label: 'Detection Engine',
            status: systemStatus.detection,
            icon: '🧠',
            description: 'YOLOv8 model inference',
        },
        {
            label: 'WebSocket',
            status: systemStatus.websocket,
            icon: '🔌',
            description: 'Real-time alert stream',
        },
        {
            label: 'GPS / Location',
            status: systemStatus.gps,
            icon: '📍',
            description: 'Geolocation services',
        },
    ];

    const performanceMetrics = [
        { label: 'Frame Rate', value: `${systemStatus.fps} FPS`, ok: systemStatus.fps >= 15 },
        { label: 'Latency', value: `${systemStatus.latency} ms`, ok: systemStatus.latency < 200 },
    ];

    return (
        <div className="settings">
            {/* Header */}
            <div className="settings__header">
                <div>
                    <h2 className="settings__title">Settings & System Status</h2>
                    <p className="settings__subtitle">Configure preferences and monitor system health</p>
                </div>
                {saved && (
                    <div className="settings__saved-toast">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Settings saved
                    </div>
                )}
            </div>

            <div className="settings__grid">
                {/* LEFT COLUMN */}
                <div className="settings__column">
                    {/* Alert Settings */}
                    <SettingsCard title="Alerts" icon="🔔">
                        <ToggleRow
                            label="Enable Alerts"
                            description="Show hazard alerts in the feed"
                            checked={settings.alertsEnabled}
                            onChange={() => handleToggle('alertsEnabled')}
                        />
                        <ToggleRow
                            label="Audio Alerts"
                            description="Play a sound for new alerts"
                            checked={settings.audioAlertsEnabled}
                            onChange={() => handleToggle('audioAlertsEnabled')}
                            disabled={!settings.alertsEnabled}
                        />
                        <SelectRow
                            label="Minimum Severity"
                            description="Only alert for this severity and above"
                            value={settings.minSeverityForAlert}
                            options={[
                                { label: 'Low', value: 'low' },
                                { label: 'Medium', value: 'medium' },
                                { label: 'High', value: 'high' },
                                { label: 'Critical', value: 'critical' },
                            ]}
                            onChange={(v) => handleChange('minSeverityForAlert', v as SeverityLevel)}
                            disabled={!settings.alertsEnabled}
                        />
                        <SliderRow
                            label="Proximity Distance"
                            description="Alert distance threshold in metres"
                            value={settings.proximityAlertDistance}
                            min={100}
                            max={2000}
                            step={100}
                            unit="m"
                            onChange={(v) => handleChange('proximityAlertDistance', v)}
                            disabled={!settings.alertsEnabled}
                        />
                    </SettingsCard>

                    {/* Display Settings */}
                    <SettingsCard title="Display" icon="🖥️">
                        <SelectRow
                            label="Speed Unit"
                            description="Unit for speed display"
                            value={settings.speedUnit}
                            options={[
                                { label: 'km/h', value: 'kmh' },
                                { label: 'mph', value: 'mph' },
                            ]}
                            onChange={(v) => handleChange('speedUnit', v as 'kmh' | 'mph')}
                        />
                        <SelectRow
                            label="Theme"
                            description="Application colour theme"
                            value={settings.theme}
                            options={[
                                { label: 'Light', value: 'light' },
                                { label: 'Dark', value: 'dark' },
                                { label: 'Auto (System)', value: 'auto' },
                            ]}
                            onChange={(v) => handleChange('theme', v as 'light' | 'dark' | 'auto')}
                        />
                        <SelectRow
                            label="Map Provider"
                            description="Source for map tiles"
                            value={settings.mapProvider}
                            options={[
                                { label: 'OpenStreetMap', value: 'osm' },
                                { label: 'Google Maps', value: 'google' },
                            ]}
                            onChange={(v) => handleChange('mapProvider', v as 'osm' | 'google')}
                        />
                    </SettingsCard>
                </div>

                {/* RIGHT COLUMN */}
                <div className="settings__column">
                    {/* System Health */}
                    <SettingsCard title="System Health" icon="❤️">
                        <div className="settings__health-list">
                            {systemHealth.map((item) => (
                                <div key={item.label} className="settings__health-item">
                                    <div className="settings__health-icon">{item.icon}</div>
                                    <div className="settings__health-info">
                                        <span className="settings__health-label">{item.label}</span>
                                        <span className="settings__health-desc">{item.description}</span>
                                    </div>
                                    <StatusPill status={item.status} />
                                </div>
                            ))}
                        </div>
                    </SettingsCard>

                    {/* Performance */}
                    <SettingsCard title="Performance" icon="⚡">
                        <div className="settings__perf-list">
                            {performanceMetrics.map((m) => (
                                <div key={m.label} className="settings__perf-item">
                                    <div className="settings__perf-info">
                                        <span className="settings__perf-label">{m.label}</span>
                                        <span
                                            className={`settings__perf-value ${m.ok ? 'settings__perf-value--ok' : 'settings__perf-value--warn'
                                                }`}
                                        >
                                            {m.value}
                                        </span>
                                    </div>
                                    <div
                                        className={`settings__perf-bar ${m.ok ? 'settings__perf-bar--ok' : 'settings__perf-bar--warn'
                                            }`}
                                    />
                                </div>
                            ))}
                        </div>
                    </SettingsCard>

                    {/* About */}
                    <SettingsCard title="About" icon="ℹ️">
                        <div className="settings__about">
                            <div className="settings__about-row">
                                <span className="settings__about-key">App Version</span>
                                <span className="settings__about-val">1.0.0</span>
                            </div>
                            <div className="settings__about-row">
                                <span className="settings__about-key">Model</span>
                                <span className="settings__about-val">YOLOv8 — pavex_v1.pt</span>
                            </div>
                            <div className="settings__about-row">
                                <span className="settings__about-key">Backend</span>
                                <span className="settings__about-val">FastAPI 0.109</span>
                            </div>
                            <div className="settings__about-row">
                                <span className="settings__about-key">Database</span>
                                <span className="settings__about-val">Supabase PostgreSQL</span>
                            </div>
                            <div className="settings__about-row">
                                <span className="settings__about-key">Frontend</span>
                                <span className="settings__about-val">React 18 + Vite 5</span>
                            </div>
                        </div>
                    </SettingsCard>
                </div>
            </div>
        </div>
    );
}

/* ─── Sub-components ─────────────────────────────────────────────────── */

function SettingsCard({
    title,
    icon,
    children,
}: {
    title: string;
    icon: string;
    children: React.ReactNode;
}) {
    return (
        <div className="settings-card">
            <div className="settings-card__header">
                <span className="settings-card__icon">{icon}</span>
                <h3 className="settings-card__title">{title}</h3>
            </div>
            <div className="settings-card__body">{children}</div>
        </div>
    );
}

function ToggleRow({
    label,
    description,
    checked,
    onChange,
    disabled,
}: {
    label: string;
    description?: string;
    checked: boolean;
    onChange: () => void;
    disabled?: boolean;
}) {
    return (
        <div className={`settings-row ${disabled ? 'settings-row--disabled' : ''}`}>
            <div className="settings-row__info">
                <span className="settings-row__label">{label}</span>
                {description && <span className="settings-row__desc">{description}</span>}
            </div>
            <button
                role="switch"
                aria-checked={checked}
                aria-label={label}
                className={`settings-toggle ${checked ? 'settings-toggle--on' : ''}`}
                onClick={onChange}
                disabled={disabled}
                type="button"
            >
                <span className="settings-toggle__thumb" />
            </button>
        </div>
    );
}

function SelectRow({
    label,
    description,
    value,
    options,
    onChange,
    disabled,
}: {
    label: string;
    description?: string;
    value: string;
    options: { label: string; value: string }[];
    onChange: (v: string) => void;
    disabled?: boolean;
}) {
    return (
        <div className={`settings-row ${disabled ? 'settings-row--disabled' : ''}`}>
            <div className="settings-row__info">
                <span className="settings-row__label">{label}</span>
                {description && <span className="settings-row__desc">{description}</span>}
            </div>
            <select
                className="settings-select"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                aria-label={label}
            >
                {options.map((o) => (
                    <option key={o.value} value={o.value}>
                        {o.label}
                    </option>
                ))}
            </select>
        </div>
    );
}

function SliderRow({
    label,
    description,
    value,
    min,
    max,
    step,
    unit,
    onChange,
    disabled,
}: {
    label: string;
    description?: string;
    value: number;
    min: number;
    max: number;
    step: number;
    unit?: string;
    onChange: (v: number) => void;
    disabled?: boolean;
}) {
    return (
        <div className={`settings-row settings-row--column ${disabled ? 'settings-row--disabled' : ''}`}>
            <div className="settings-row__info">
                <span className="settings-row__label">{label}</span>
                {description && <span className="settings-row__desc">{description}</span>}
            </div>
            <div className="settings-slider">
                <input
                    type="range"
                    className="settings-slider__input"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    disabled={disabled}
                    aria-label={label}
                />
                <span className="settings-slider__value">
                    {value}{unit}
                </span>
            </div>
        </div>
    );
}

function StatusPill({ status }: { status: string }) {
    const isGood =
        status === 'connected' || status === 'active' || status === 'available';
    const isWarn = status === 'reconnecting' || status === 'paused';

    return (
        <span
            className={`settings__status-pill ${isGood
                    ? 'settings__status-pill--ok'
                    : isWarn
                        ? 'settings__status-pill--warn'
                        : 'settings__status-pill--error'
                }`}
        >
            <span className="settings__status-dot" />
            {status}
        </span>
    );
}