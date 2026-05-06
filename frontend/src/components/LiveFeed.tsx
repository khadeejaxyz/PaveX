/**
 * LiveFeed Component
 * Displays live camera feed with real-time hazard detection overlays
 * FIXED: Properly renders bbox array format [x1, y1, x2, y2]
 */

import { useEffect, useRef } from 'react';
import { useMediaStream, useDetection, useFPS } from '../hooks';
import { useStore } from '../store/useStore';
import type { LiveFeedProps, Detection } from '../types';
import './LiveFeed.css';

export default function LiveFeed({ onDetection, videoSrc = null, className = '' }: LiveFeedProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
    const animationFrameRef = useRef<number>();
    const lastDetectionTimeRef = useRef(0);
    const detectionInFlightRef = useRef(false);

    const { stream, error: streamError } = useMediaStream(undefined, !videoSrc);
    const { detectVideoFrame } = useDetection();
    const { fps, recordFrame } = useFPS();

    const currentDetections = useStore((state) => state.currentDetections);
    const isDetecting = useStore((state) => state.isDetecting);
    const inputSource = useStore((state) => state.inputSource);

    const cameraDetectionInterval = 500; // Camera stays live while backend samples periodically.
    const videoFrameDelay = 30; // Mirrors backend video_stream.py cv2.waitKey(30).
    const videoFrameStepSeconds = videoFrameDelay / 1000;

    // Setup video stream
    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        if (videoSrc) {
            video.srcObject = null;
            video.src = videoSrc;
            video.loop = true;
            video.playbackRate = 1;
            video.pause();
            return;
        }

        if (stream) {
            video.removeAttribute('src');
            video.playbackRate = 1;
            video.srcObject = stream;
        }
    }, [stream, videoSrc]);

    // Main animation loop
    useEffect(() => {
        if (!videoRef.current || !canvasRef.current || !overlayCanvasRef.current) {
            return;
        }

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const overlayCanvas = overlayCanvasRef.current;
        const ctx = canvas.getContext('2d');
        const overlayCtx = overlayCanvas.getContext('2d');

        if (!ctx || !overlayCtx) return;

        const render = async () => {
            recordFrame();

            // Draw video frame to canvas
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const displayWidth = overlayCanvas.clientWidth || video.clientWidth || video.videoWidth;
                const displayHeight = overlayCanvas.clientHeight || video.clientHeight || video.videoHeight;
                overlayCanvas.width = displayWidth;
                overlayCanvas.height = displayHeight;

                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                // Run detection at intervals
                const now = Date.now();
                const isUploadedVideo = inputSource === 'video' && Boolean(videoSrc);
                const detectionInterval = isUploadedVideo ? videoFrameDelay : cameraDetectionInterval;

                if (
                    !detectionInFlightRef.current &&
                    now - lastDetectionTimeRef.current >= detectionInterval &&
                    (inputSource === 'camera' || inputSource === 'video')
                ) {
                    detectionInFlightRef.current = true;
                    lastDetectionTimeRef.current = now;

                    if (isUploadedVideo) {
                        video.pause();
                    }

                    try {
                        const detections = await detectVideoFrame(canvas);
                        detections?.forEach((detection) => onDetection?.(detection));
                    } finally {
                        detectionInFlightRef.current = false;

                        if (isUploadedVideo && Number.isFinite(video.duration)) {
                            const nextTime = video.currentTime + videoFrameStepSeconds;
                            video.currentTime = nextTime >= video.duration ? 0 : nextTime;
                        }
                    }
                }

                // Draw detection overlays
                drawDetections(
                    overlayCtx,
                    currentDetections,
                    video.videoWidth,
                    video.videoHeight,
                    displayWidth,
                    displayHeight,
                    getObjectFit(video)
                );
            }

            animationFrameRef.current = requestAnimationFrame(render);
        };

        render();

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [currentDetections, detectVideoFrame, recordFrame, inputSource, videoSrc]);

    return (
        <div className={`live-feed ${className}`}>
            <div className="live-feed__container">
                {/* Video Element */}
                <video
                    ref={videoRef}
                    autoPlay
                    controls={Boolean(videoSrc)}
                    playsInline
                    muted
                    className="live-feed__video"
                />

                {/* Hidden canvas for detection */}
                <canvas
                    ref={canvasRef}
                    className="live-feed__canvas--hidden"
                />

                {/* Overlay canvas for bounding boxes */}
                <canvas
                    ref={overlayCanvasRef}
                    className="live-feed__canvas--overlay"
                />

                {/* Status Overlay */}
                <div className="live-feed__status">
                    <div className="live-feed__status-item">
                        <span className="live-feed__status-label">FPS</span>
                        <span className="live-feed__status-value">{fps}</span>
                    </div>
                    <div className="live-feed__status-item">
                        <span className="live-feed__status-label">Detections</span>
                        <span className="live-feed__status-value">{currentDetections.length}</span>
                    </div>
                    <div className="live-feed__status-item">
                        <div className={`live-feed__status-indicator ${isDetecting ? 'active' : ''}`} />
                        <span className="live-feed__status-label">
                            {isDetecting ? 'Detecting...' : 'Ready'}
                        </span>
                    </div>
                </div>

                {/* Error Message */}
                {streamError && (
                    <div className="live-feed__error">
                        <svg className="live-feed__error-icon" viewBox="0 0 24 24" fill="none">
                            <path
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </svg>
                        <p className="live-feed__error-text">{streamError}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

/**
 * Draw detection bounding boxes and labels
 * FIXED: Properly handles bbox array format [x1, y1, x2, y2]
 */
function drawDetections(
    ctx: CanvasRenderingContext2D,
    detections: Detection[],
    sourceWidth: number,
    sourceHeight: number,
    displayWidth: number,
    displayHeight: number,
    objectFit: string
) {
    ctx.clearRect(0, 0, displayWidth, displayHeight);

    if (!sourceWidth || !sourceHeight || !displayWidth || !displayHeight) {
        return;
    }

    const scale = objectFit === 'cover'
        ? Math.max(displayWidth / sourceWidth, displayHeight / sourceHeight)
        : Math.min(displayWidth / sourceWidth, displayHeight / sourceHeight);
    const offsetX = (displayWidth - sourceWidth * scale) / 2;
    const offsetY = (displayHeight - sourceHeight * scale) / 2;

    detections.forEach((detection) => {
        // CRITICAL FIX: bbox is now [x1, y1, x2, y2] array
        const [rawX1, rawY1, rawX2, rawY2] = detection.bbox;
        const x1 = clamp(rawX1 * scale + offsetX, 0, displayWidth);
        const y1 = clamp(rawY1 * scale + offsetY, 0, displayHeight);
        const x2 = clamp(rawX2 * scale + offsetX, 0, displayWidth);
        const y2 = clamp(rawY2 * scale + offsetY, 0, displayHeight);
        const boxWidth = x2 - x1;
        const boxHeight = y2 - y1;

        if (boxWidth <= 0 || boxHeight <= 0) {
            return;
        }

        // Get color based on severity
        const color = getSeverityColor(detection.severity);

        // Draw bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(x1, y1, boxWidth, boxHeight);

        // Draw filled corner markers
        const markerSize = 12;
        ctx.fillStyle = color;

        // Top-left
        ctx.fillRect(x1 - 1, y1 - 1, markerSize, 3);
        ctx.fillRect(x1 - 1, y1 - 1, 3, markerSize);

        // Top-right
        ctx.fillRect(x2 - markerSize + 1, y1 - 1, markerSize, 3);
        ctx.fillRect(x2 - 2, y1 - 1, 3, markerSize);

        // Bottom-left
        ctx.fillRect(x1 - 1, y2 - 2, markerSize, 3);
        ctx.fillRect(x1 - 1, y2 - markerSize + 1, 3, markerSize);

        // Bottom-right
        ctx.fillRect(x2 - markerSize + 1, y2 - 2, markerSize, 3);
        ctx.fillRect(x2 - 2, y2 - markerSize + 1, 3, markerSize);

        // Draw label background
        const label = `${formatHazardType(detection.hazardType)} ${Math.round(detection.confidence * 100)}%`;
        ctx.font = 'bold 14px Inter, sans-serif';
        const textMetrics = ctx.measureText(label);
        const labelWidth = textMetrics.width + 16;
        const labelHeight = 28;

        ctx.fillStyle = color;
        const labelY = Math.max(0, y1 - labelHeight - 4);
        ctx.fillRect(x1, labelY, Math.min(labelWidth, displayWidth - x1), labelHeight);

        // Draw label text
        ctx.fillStyle = '#FFFFFF';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, x1 + 8, labelY + labelHeight / 2);

        // Draw severity badge
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        const badgeY = Math.min(displayHeight - 24, y1 + boxHeight + 8);
        ctx.fillRect(x1, badgeY, 80, 24);

        ctx.fillStyle = color;
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.textBaseline = 'middle';
        ctx.fillText(detection.severity.toUpperCase(), x1 + 8, badgeY + 12);
    });
}

/**
 * Get color for severity level
 */
function getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
        low: '#22C55E',      // green
        medium: '#F59E0B',   // amber
        high: '#EF4444',     // red
        critical: '#DC2626', // dark red
    };
    return colors[severity] || '#94A3B8';
}

/**
 * Format hazard type for display
 */
function formatHazardType(type: string): string {
    return type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function getObjectFit(video: HTMLVideoElement): string {
    return window.getComputedStyle(video).objectFit || 'contain';
}

function clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(value, max));
}
