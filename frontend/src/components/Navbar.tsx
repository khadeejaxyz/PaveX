/**
 * Navbar — persistent top navigation across dashboard pages
 */

import { NavLink } from 'react-router-dom';
import { useStore } from '../store/useStore';
import './Navbar.css';

const NAV_ITEMS = [
    { to: '/dashboard', label: 'Dashboard', icon: '⬛' },
    { to: '/analytics', label: 'Analytics', icon: '📊' },
    { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Navbar() {
    const systemStatus = useStore((s) => s.systemStatus);
    const unacknowledgedAlerts = useStore((s) => s.unacknowledgedAlerts);

    const wsOk = systemStatus.websocket === 'connected';

    return (
        <nav className="navbar">
            {/* Brand */}
            <NavLink to="/" className="navbar__brand">
                <svg className="navbar__brand-icon" viewBox="0 0 32 32" fill="none">
                    <rect width="32" height="32" rx="8" fill="var(--color-primary-600)" />
                    <path d="M8 22l4-8 4 6 3-4 5 6" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span className="navbar__brand-name">PaveX</span>
            </NavLink>

            {/* Nav links */}
            <div className="navbar__links">
                {NAV_ITEMS.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) =>
                            `navbar__link ${isActive ? 'navbar__link--active' : ''}`
                        }
                    >
                        <span className="navbar__link-icon">{item.icon}</span>
                        <span className="navbar__link-label">{item.label}</span>
                    </NavLink>
                ))}
            </div>

            {/* Right side */}
            <div className="navbar__right">
                {/* Live status */}
                <div className={`navbar__ws-badge ${wsOk ? 'navbar__ws-badge--ok' : ''}`}>
                    <span className="navbar__ws-dot" />
                    <span>{wsOk ? 'Live' : 'Offline'}</span>
                </div>

                {/* Alert bell */}
                <div className="navbar__bell">
                    <svg viewBox="0 0 24 24" fill="none">
                        <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {unacknowledgedAlerts > 0 && (
                        <span className="navbar__bell-count">{unacknowledgedAlerts}</span>
                    )}
                </div>
            </div>
        </nav>
    );
}
