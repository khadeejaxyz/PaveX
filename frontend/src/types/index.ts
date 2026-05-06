/**
 * PaveX TypeScript Type Definitions
 */

// Hazard Types
export type HazardType = 'pothole' | 'speed_hump' | 'crack' | 'debris' | 'other';

// Severity Levels - FIXED: Added 'critical' to match backend
export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

// Detection Status
export type DetectionStatus = 'active' | 'processing' | 'idle' | 'error';

// Input Source
export type InputSource = 'camera' | 'video' | 'image';

// Location
export interface Location {
    latitude: number;
    longitude: number;
    accuracy?: number;
    timestamp?: string;
}

// Detection Result - FIXED: bbox is now array format [x1, y1, x2, y2]
export interface Detection {
    id: string;
    hazardType: HazardType;
    confidence: number;
    bbox: [number, number, number, number]; // [x1, y1, x2, y2]
    severity: SeverityLevel;
    timestamp: string;
    location?: Location;
    imageUrl?: string;
}

// Hazard Event (Database Model)
export interface HazardEvent {
    id: string;
    hazardType: HazardType;
    severity: SeverityLevel;
    confidence: number;
    location: Location;
    detectedAt: string;
    imageUrl?: string;
    videoUrl?: string;
    verified: boolean;
    reportCount: number;
    metadata?: Record<string, any>;
}

// Alert
export interface Alert {
    id: string;
    hazardType: HazardType;
    severity: SeverityLevel;
    message: string;
    location: Location;
    distance?: number; // meters
    timestamp: string;
    acknowledged: boolean;
}

// Speed Recommendation
export interface SpeedRecommendation {
    current: number;
    recommended: number;
    maxSafe: number;
    reason: string;
}

// System Status
export interface SystemStatus {
    camera: 'connected' | 'disconnected' | 'error';
    detection: 'active' | 'paused' | 'error';
    websocket: 'connected' | 'disconnected' | 'reconnecting';
    gps: 'available' | 'unavailable';
    fps: number;
    latency: number;
}

// Statistics
export interface Statistics {
    totalDetections: number;
    todayDetections: number;
    averageConfidence: number;
    severityDistribution: Record<SeverityLevel, number>;
    hazardTypeDistribution: Record<HazardType, number>;
    detectionsByHour: number[];
}

// User Settings
export interface UserSettings {
    alertsEnabled: boolean;
    audioAlertsEnabled: boolean;
    minSeverityForAlert: SeverityLevel;
    proximityAlertDistance: number; // meters
    speedUnit: 'kmh' | 'mph';
    theme: 'light' | 'dark' | 'auto';
    mapProvider: 'google' | 'osm';
}

// API Response Types
export interface DetectionResponse {
    success: boolean;
    detections: Detection[];
    metadata: {
        processingTime: number;
        frameSize: [number, number];
        modelVersion: string;
    };
}

export interface HazardsResponse {
    success: boolean;
    hazards: HazardEvent[];
    total: number;
    page: number;
    pageSize: number;
}

export interface StatsResponse {
    success: boolean;
    statistics: Statistics;
}

// WebSocket Message Types
export interface WSMessage {
    type: 'hazard_alert' | 'system_status' | 'detection_update' | 'connection';
    data: any;
    timestamp: string;
}

export interface WSHazardAlert {
    type: 'hazard_alert';
    data: Alert;
    timestamp: string;
}

export interface WSSystemStatus {
    type: 'system_status';
    data: SystemStatus;
    timestamp: string;
}

// Store State
export interface AppState {
    // Detection State
    currentDetections: Detection[];
    detectionHistory: Detection[];
    isDetecting: boolean;
    inputSource: InputSource;

    // Alerts
    alerts: Alert[];
    unacknowledgedAlerts: number;

    // Location & Navigation
    currentLocation: Location | null;
    nearbyHazards: HazardEvent[];

    // System Status
    systemStatus: SystemStatus;

    // Statistics
    statistics: Statistics | null;

    // Settings
    settings: UserSettings;

    // UI State
    selectedHazard: HazardEvent | null;
    isMapExpanded: boolean;
    isSidebarOpen: boolean;
}

// Store Actions
export interface AppActions {
    // Detection Actions
    setDetections: (detections: Detection[]) => void;
    addDetection: (detection: Detection) => void;
    clearDetections: () => void;
    setDetecting: (isDetecting: boolean) => void;
    setInputSource: (source: InputSource) => void;

    // Alert Actions
    addAlert: (alert: Alert) => void;
    acknowledgeAlert: (id: string) => void;
    clearAlerts: () => void;

    // Location Actions
    setCurrentLocation: (location: Location) => void;
    setNearbyHazards: (hazards: HazardEvent[]) => void;

    // System Status Actions
    updateSystemStatus: (status: Partial<SystemStatus>) => void;

    // Statistics Actions
    setStatistics: (stats: Statistics) => void;

    // Settings Actions
    updateSettings: (settings: Partial<UserSettings>) => void;

    // UI Actions
    selectHazard: (hazard: HazardEvent | null) => void;
    toggleMap: () => void;
    toggleSidebar: () => void;
}

// Component Props
export interface LiveFeedProps {
    onDetection?: (detection: Detection) => void;
    videoSrc?: string | null;
    className?: string;
}

export interface MapPanelProps {
    hazards: HazardEvent[];
    currentLocation?: Location;
    selectedHazard?: HazardEvent | null;
    onHazardSelect?: (hazard: HazardEvent) => void;
    className?: string;
}

export interface AlertFeedProps {
    alerts: Alert[];
    onAcknowledge?: (id: string) => void;
    className?: string;
}

export interface SpeedMeterProps {
    current: number;
    recommended: number;
    maxSafe: number;
    unit?: 'kmh' | 'mph';
    className?: string;
}

export interface HazardCardProps {
    hazard: Detection | HazardEvent;
    onSelect?: () => void;
    className?: string;
}

export interface StatsCardProps {
    title: string;
    value: string | number;
    change?: number;
    icon?: React.ReactNode;
    trend?: 'up' | 'down' | 'neutral';
    className?: string;
}
