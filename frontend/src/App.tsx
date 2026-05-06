/**
 * PaveX Root Application — with React Router
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useGeolocation, useWebSocket } from './hooks';
import { api } from './services/api';
import { useStore } from './store/useStore';

import Navbar from './components/Navbar';
import Welcome from './components/Welcome';
import Dashboard from './components/Dashboard';
import Analytics from './components/Analytics';
import Settings from './components/Settings';

import './App.css';

function AppLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="app-layout">
            <Navbar />
            <main className="app-layout__content">{children}</main>
        </div>
    );
}

function GlobalInit() {
    useGeolocation();
    useWebSocket();
    const setStatistics = useStore((s) => s.setStatistics);

    useEffect(() => {
        api.getStatistics().then((stats) => {
            if (stats) setStatistics(stats);
        });
    }, [setStatistics]);

    return null;
}

export default function App() {
    return (
        <BrowserRouter>
            <GlobalInit />
            <Routes>
                <Route path="/" element={<Welcome />} />
                <Route path="/dashboard" element={<AppLayout><Dashboard /></AppLayout>} />
                <Route path="/analytics" element={<AppLayout><Analytics /></AppLayout>} />
                <Route path="/settings" element={<AppLayout><Settings /></AppLayout>} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    );
}