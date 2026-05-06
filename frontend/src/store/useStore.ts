/**
 * PaveX Global State Store
 * Using Zustand for simple, performant state management
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { AppState, AppActions } from '../types';

// Initial state
const initialState: AppState = {
    // Detection State
    currentDetections: [],
    detectionHistory: [],
    isDetecting: false,
    inputSource: 'camera',

    // Alerts
    alerts: [],
    unacknowledgedAlerts: 0,

    // Location & Navigation
    currentLocation: null,
    nearbyHazards: [],

    // System Status
    systemStatus: {
        camera: 'disconnected',
        detection: 'active',
        websocket: 'disconnected',
        gps: 'unavailable',
        fps: 0,
        latency: 0,
    },

    // Statistics
    statistics: null,

    // Settings
    settings: {
        alertsEnabled: true,
        audioAlertsEnabled: true,
        minSeverityForAlert: 'medium',
        proximityAlertDistance: 500, // meters
        speedUnit: 'kmh',
        theme: 'light',
        mapProvider: 'osm',
    },

    // UI State
    selectedHazard: null,
    isMapExpanded: false,
    isSidebarOpen: true,
};

// Create store
export const useStore = create<AppState & AppActions>()(
    devtools(
        persist(
            (set) => ({
                ...initialState,

                // Detection Actions
                setDetections: (detections) =>
                    set({ currentDetections: detections }),

                addDetection: (detection) =>
                    set((state) => ({
                        currentDetections: [...state.currentDetections, detection],
                        detectionHistory: [detection, ...state.detectionHistory].slice(0, 100), // Keep last 100
                    })),

                clearDetections: () =>
                    set({ currentDetections: [] }),

                setDetecting: (isDetecting) =>
                    set({ isDetecting }),

                setInputSource: (source) =>
                    set({ inputSource: source }),

                // Alert Actions
                addAlert: (alert) =>
                    set((state) => ({
                        alerts: [alert, ...state.alerts].slice(0, 50), // Keep last 50
                        unacknowledgedAlerts: state.unacknowledgedAlerts + 1,
                    })),

                acknowledgeAlert: (id) =>
                    set((state) => ({
                        alerts: state.alerts.map((alert) =>
                            alert.id === id ? { ...alert, acknowledged: true } : alert
                        ),
                        unacknowledgedAlerts: Math.max(0, state.unacknowledgedAlerts - 1),
                    })),

                clearAlerts: () =>
                    set({ alerts: [], unacknowledgedAlerts: 0 }),

                // Location Actions
                setCurrentLocation: (location) =>
                    set({ currentLocation: location }),

                setNearbyHazards: (hazards) =>
                    set({ nearbyHazards: hazards }),

                // System Status Actions
                updateSystemStatus: (status) =>
                    set((state) => ({
                        systemStatus: { ...state.systemStatus, ...status },
                    })),

                // Statistics Actions
                setStatistics: (stats) =>
                    set({ statistics: stats }),

                // Settings Actions
                updateSettings: (settings) =>
                    set((state) => ({
                        settings: { ...state.settings, ...settings },
                    })),

                // UI Actions
                selectHazard: (hazard) =>
                    set({ selectedHazard: hazard }),

                toggleMap: () =>
                    set((state) => ({ isMapExpanded: !state.isMapExpanded })),

                toggleSidebar: () =>
                    set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
            }),
            {
                name: 'pavex-storage',
                // Only persist settings and UI preferences
                partialize: (state) => ({
                    settings: state.settings,
                    isSidebarOpen: state.isSidebarOpen,
                }),
            }
        ),
        { name: 'PaveX Store' }
    )
);

// Selectors for common queries
export const selectCurrentDetections = (state: AppState) => state.currentDetections;
export const selectActiveAlerts = (state: AppState) =>
    state.alerts.filter(alert => !alert.acknowledged);
export const selectHighSeverityDetections = (state: AppState) =>
    state.currentDetections.filter(d => d.severity === 'high' || d.severity === 'critical');
export const selectSystemHealth = (state: AppState) => {
    const { camera, detection, websocket, gps } = state.systemStatus;
    const healthy = [camera, detection, websocket, gps].filter(
        status => status === 'connected' || status === 'active' || status === 'available'
    ).length;
    return (healthy / 4) * 100; // Health percentage
};
