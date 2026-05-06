/**
 * PaveX Custom React Hooks
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useStore } from '../store/useStore';
import { api } from '../services/api';
import { websocket } from '../services/websocket';
import type { Location, Alert, WSMessage } from '../types';

/**
 * Hook for managing geolocation
 */
export function useGeolocation() {
    const setCurrentLocation = useStore((state) => state.setCurrentLocation);
    const updateSystemStatus = useStore((state) => state.updateSystemStatus);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!navigator.geolocation) {
            setError('Geolocation not supported');
            updateSystemStatus({ gps: 'unavailable' });
            return;
        }

        const watchId = navigator.geolocation.watchPosition(
            (position) => {
                const location: Location = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: new Date(position.timestamp).toISOString(),
                };
                setCurrentLocation(location);
                updateSystemStatus({ gps: 'available' });
                setError(null);
            },
            (err) => {
                setError(err.message);
                updateSystemStatus({ gps: 'unavailable' });
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0,
            }
        );

        return () => navigator.geolocation.clearWatch(watchId);
    }, [setCurrentLocation, updateSystemStatus]);

    return { error };
}

/**
 * Hook for managing WebSocket connection
 */
export function useWebSocket() {
    const addAlert = useStore((state) => state.addAlert);
    const updateSystemStatus = useStore((state) => state.updateSystemStatus);
    const settings = useStore((state) => state.settings);

    useEffect(() => {
        // Handle connection status
        const unsubConnection = websocket.onConnectionChange((connected) => {
            updateSystemStatus({
                websocket: connected ? 'connected' : 'disconnected',
            });
        });

        // Handle messages
        const unsubMessage = websocket.onMessage((message: WSMessage) => {
            if (message.type === 'hazard_alert' && settings.alertsEnabled) {
                const alert = message.data as Alert;

                // Filter by minimum severity
                const severityLevel = ['low', 'medium', 'high', 'critical'];
                const minLevel = severityLevel.indexOf(settings.minSeverityForAlert);
                const alertLevel = severityLevel.indexOf(alert.severity);

                if (alertLevel >= minLevel) {
                    addAlert(alert);

                    // Play audio alert if enabled
                    if (settings.audioAlertsEnabled) {
                        playAlertSound(alert.severity);
                    }
                }
            } else if (message.type === 'system_status') {
                updateSystemStatus(message.data);
            }
        });

        return () => {
            unsubConnection();
            unsubMessage();
        };
    }, [addAlert, updateSystemStatus, settings]);
}

/**
 * Hook for camera/video stream
 */
export function useMediaStream(constraints?: MediaStreamConstraints, enabled = true) {
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string | null>(null);
    const updateSystemStatus = useStore((state) => state.updateSystemStatus);

    useEffect(() => {
        if (!enabled) {
            if (stream) {
                stream.getTracks().forEach((track) => track.stop());
            }
            setStream(null);
            setError(null);
            updateSystemStatus({ camera: 'disconnected' });
            return;
        }

        let mounted = true;

        async function getStream() {
            try {
                const mediaStream = await navigator.mediaDevices.getUserMedia(
                    constraints || {
                        video: {
                            width: { ideal: 1280 },
                            height: { ideal: 720 },
                            facingMode: 'environment',
                        },
                        audio: false,
                    }
                );

                if (mounted) {
                    setStream(mediaStream);
                    updateSystemStatus({ camera: 'connected' });
                    setError(null);
                }
            } catch (err) {
                if (mounted) {
                    setError(err instanceof Error ? err.message : 'Failed to access camera');
                    updateSystemStatus({ camera: 'error' });
                }
            }
        }

        getStream();

        return () => {
            mounted = false;
            if (stream) {
                stream.getTracks().forEach((track) => track.stop());
            }
        };
    }, [enabled, updateSystemStatus]);

    return { stream, error };
}

/**
 * Hook for detection processing
 */
export function useDetection() {
    const currentLocation = useStore((state) => state.currentLocation);
    const addDetection = useStore((state) => state.addDetection);
    const setDetections = useStore((state) => state.setDetections);
    const setDetecting = useStore((state) => state.setDetecting);
    const [isProcessing, setIsProcessing] = useState(false);

    const detectImage = useCallback(
        async (file: File) => {
            setIsProcessing(true);
            setDetecting(true);

            try {
                const response = await api.detectImage(file, currentLocation || undefined);

                response.detections.forEach((detection) => {
                    addDetection(detection);
                    // Save to backend for persistence
                    api.saveDetection(detection);
                });

                return response.detections;
            } catch (error) {
                console.error('Detection error:', error);
                throw error;
            } finally {
                setIsProcessing(false);
                setDetecting(false);
            }
        },
        [currentLocation, addDetection, setDetecting]
    );

    const detectVideoFrame = useCallback(
        async (canvas: HTMLCanvasElement) => {
            if (isProcessing) return;

            setIsProcessing(true);

            try {
                const blob = await new Promise<Blob>((resolve) => {
                    canvas.toBlob((blob) => resolve(blob!), 'image/jpeg', 0.8);
                });

                const response = await api.detectVideoFrame(blob, currentLocation || undefined);

                setDetections(response.detections);
                response.detections.forEach((detection) => api.saveDetection(detection));

                return response.detections;
            } catch (error) {
                console.error('Video detection error:', error);
            } finally {
                setIsProcessing(false);
            }
        },
        [currentLocation, setDetections, isProcessing]
    );

    return { detectImage, detectVideoFrame, isProcessing };
}

/**
 * Hook for FPS calculation
 */
export function useFPS() {
    const [fps, setFps] = useState(0);
    const frameTimesRef = useRef<number[]>([]);
    const updateSystemStatus = useStore((state) => state.updateSystemStatus);

    const recordFrame = useCallback(() => {
        const now = performance.now();
        frameTimesRef.current.push(now);

        // Keep only last 60 frames
        if (frameTimesRef.current.length > 60) {
            frameTimesRef.current.shift();
        }

        // Calculate FPS
        if (frameTimesRef.current.length >= 2) {
            const duration =
                now - frameTimesRef.current[0];
            const currentFps = Math.round(
                (frameTimesRef.current.length / duration) * 1000
            );
            setFps(currentFps);
            updateSystemStatus({ fps: currentFps });
        }
    }, [updateSystemStatus]);

    return { fps, recordFrame };
}

/**
 * Hook for reduced motion preference
 */
export function useReducedMotion() {
    const [prefersReducedMotion, setPrefersReducedMotion] = useState(
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );

    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);

        mediaQuery.addEventListener('change', handler);
        return () => mediaQuery.removeEventListener('change', handler);
    }, []);

    return prefersReducedMotion;
}

/**
 * Hook for intersection observer (for animations)
 */
export function useIntersectionObserver(
    options?: IntersectionObserverInit
) {
    const [isIntersecting, setIsIntersecting] = useState(false);
    const [hasIntersected, setHasIntersected] = useState(false);
    const ref = useRef<HTMLElement>(null);

    useEffect(() => {
        const element = ref.current;
        if (!element) return;

        const observer = new IntersectionObserver(([entry]) => {
            setIsIntersecting(entry.isIntersecting);
            if (entry.isIntersecting) {
                setHasIntersected(true);
            }
        }, options);

        observer.observe(element);

        return () => observer.disconnect();
    }, [options]);

    return { ref, isIntersecting, hasIntersected };
}

/**
 * Helper function to play alert sounds
 */
function playAlertSound(severity: string) {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Different frequencies for different severities
    const frequencies: Record<string, number> = {
        low: 400,
        medium: 600,
        high: 800,
        critical: 1000,
    };

    oscillator.frequency.value = frequencies[severity] || 600;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(
        0.01,
        audioContext.currentTime + 0.5
    );

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}
