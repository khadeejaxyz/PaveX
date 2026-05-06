/**
 * PaveX API Service
 * Handles all backend communication with proper error handling
 */

import type {
    Detection,
    HazardEvent,
    DetectionResponse,
    HazardsResponse,
    StatsResponse,
    Location,
    Statistics
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function transformHazardEvent(hazard: any): HazardEvent {
    const latitude = hazard.latitude ?? hazard.location?.latitude ?? 0;
    const longitude = hazard.longitude ?? hazard.location?.longitude ?? 0;

    return {
        id: hazard.id,
        hazardType: hazard.hazard_type ?? hazard.hazardType,
        severity: hazard.severity,
        confidence: hazard.confidence,
        location: {
            latitude,
            longitude,
            timestamp: hazard.captured_at ?? hazard.detectedAt,
        },
        detectedAt: hazard.captured_at ?? hazard.detectedAt ?? new Date().toISOString(),
        verified: hazard.verified ?? false,
        reportCount: hazard.report_count ?? hazard.reportCount ?? 1,
        metadata: hazard.metadata ?? {},
    };
}

class APIService {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    /**
     * Health check
     */
    async healthCheck(): Promise<boolean> {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    /**
     * Detect hazards in an image
     * FIXED: Now properly handles bbox array format [x1, y1, x2, y2]
     */
    async detectImage(
        file: File,
        location?: Location
    ): Promise<DetectionResponse> {
        try {
            const formData = new FormData();
            formData.append('file', file);
            const params = new URLSearchParams();

            if (location) {
                params.set('latitude', location.latitude.toString());
                params.set('longitude', location.longitude.toString());
            }

            const query = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${this.baseUrl}/detect${query}`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Detection failed: ${response.statusText}`);
            }

            const data = await response.json();

            // Transform backend response to frontend format
            const transformedDetections: Detection[] = (data.detections || []).map((det: any) => ({
                id: det.id || crypto.randomUUID(),
                hazardType: det.class || det.class_name || det.hazardType,
                confidence: det.confidence,
                // CRITICAL FIX: Convert bbox object {x, y, width, height} to array [x1, y1, x2, y2]
                bbox: det.bbox
                    ? Array.isArray(det.bbox)
                        ? det.bbox // Already in array format
                        : [
                            det.bbox.x,
                            det.bbox.y,
                            det.bbox.x + det.bbox.width,
                            det.bbox.y + det.bbox.height
                        ]
                    : [0, 0, 0, 0],
                severity: det.severity,
                timestamp: det.timestamp || det.location_timestamp || new Date().toISOString(),
                location: det.latitude && det.longitude
                    ? { latitude: det.latitude, longitude: det.longitude }
                    : location,
            }));

            return {
                success: true,
                detections: transformedDetections,
                metadata: data.metadata || {
                    processingTime: data.processing_time_ms || 0,
                    frameSize: [640, 640],
                    modelVersion: 'v1.0',
                },
            };
        } catch (error) {
            console.error('Detection error:', error);
            throw error;
        }
    }

    /**
     * Detect hazards in video frame
     */
    async detectVideoFrame(
        frameData: Blob,
        location?: Location
    ): Promise<DetectionResponse> {
        const file = new File([frameData], 'frame.jpg', { type: 'image/jpeg' });
        return this.detectImage(file, location);
    }

    /**
     * Get nearby hazards
     */
    async getNearbyHazards(
        latitude: number,
        longitude: number,
        radius: number = 1000 // meters
    ): Promise<HazardEvent[]> {
        try {
            const response = await fetch(
                `${this.baseUrl}/hazards/nearby?` +
                new URLSearchParams({
                    latitude: latitude.toString(),
                    longitude: longitude.toString(),
                    radius_meters: radius.toString(),
                })
            );

            if (!response.ok) {
                throw new Error(`Failed to fetch nearby hazards: ${response.statusText}`);
            }

            const data: HazardsResponse | any[] = await response.json();
            const hazards = Array.isArray(data) ? data : data.hazards || [];
            return hazards.map(transformHazardEvent);
        } catch (error) {
            console.error('Error fetching nearby hazards:', error);
            return [];
        }
    }

    /**
     * Get hazard by ID
     */
    async getHazard(id: string): Promise<HazardEvent | null> {
        try {
            const response = await fetch(`${this.baseUrl}/hazards/${id}`);

            if (!response.ok) {
                throw new Error(`Failed to fetch hazard: ${response.statusText}`);
            }

            const data = await response.json();
            const hazard = data.hazard || data;
            return hazard ? transformHazardEvent(hazard) : null;
        } catch (error) {
            console.error('Error fetching hazard:', error);
            return null;
        }
    }

    /**
     * Get statistics
     */
    async getStatistics(): Promise<Statistics | null> {
        try {
            const response = await fetch(`${this.baseUrl}/statistics`);

            if (!response.ok) {
                throw new Error(`Failed to fetch statistics: ${response.statusText}`);
            }

            const data: StatsResponse = await response.json();
            return data.statistics || null;
        } catch (error) {
            console.error('Error fetching statistics:', error);
            return null;
        }
    }

    /**
     * Report a hazard
     */
    async reportHazard(hazard: Partial<HazardEvent>): Promise<HazardEvent | null> {
        try {
            const response = await fetch(`${this.baseUrl}/hazards`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    hazard_type: hazard.hazardType,
                    severity: hazard.severity,
                    confidence: hazard.confidence,
                    latitude: hazard.location?.latitude,
                    longitude: hazard.location?.longitude,
                    detected_at: hazard.detectedAt,
                    metadata: hazard.metadata,
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to report hazard: ${response.statusText}`);
            }

            const data = await response.json();
            const savedHazard = data.hazard || data;
            return savedHazard ? transformHazardEvent(savedHazard) : null;
        } catch (error) {
            console.error('Error reporting hazard:', error);
            return null;
        }
    }

    /**
     * Update hazard
     */
    async updateHazard(
        id: string,
        updates: Partial<HazardEvent>
    ): Promise<HazardEvent | null> {
        try {
            const response = await fetch(`${this.baseUrl}/hazards/${id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updates),
            });

            if (!response.ok) {
                throw new Error(`Failed to update hazard: ${response.statusText}`);
            }

            const data = await response.json();
            const hazard = data.hazard || data;
            return hazard ? transformHazardEvent(hazard) : null;
        } catch (error) {
            console.error('Error updating hazard:', error);
            return null;
        }
    }

    /**
     * Delete hazard
     */
    async deleteHazard(id: string): Promise<boolean> {
        try {
            const response = await fetch(`${this.baseUrl}/hazards/${id}`, {
                method: 'DELETE',
            });

            return response.ok;
        } catch (error) {
            console.error('Error deleting hazard:', error);
            return false;
        }
    }

    /**
     * Upload detection to backend (for persistence)
     */
    async saveDetection(detection: Detection): Promise<boolean> {
        try {
            const hazardEvent: Partial<HazardEvent> = {
                hazardType: detection.hazardType,
                severity: detection.severity,
                confidence: detection.confidence,
                location: detection.location!,
                detectedAt: detection.timestamp,
                verified: false,
                reportCount: 1,
                metadata: {
                    bbox: detection.bbox,
                },
            };

            const result = await this.reportHazard(hazardEvent);
            return result !== null;
        } catch (error) {
            console.error('Error saving detection:', error);
            return false;
        }
    }
}

// Export singleton instance
export const api = new APIService();

// Export class for testing
export default APIService;
