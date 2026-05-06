/**
 * MapPanel Component
 * Displays hazard locations on an interactive map
 */

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { MapPanelProps } from '../types';
import './MapPanel.css';

// Fix Leaflet default marker icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function MapPanel({
    hazards,
    currentLocation,
    selectedHazard,
    onHazardSelect,
    className = '',
}: MapPanelProps) {
    const mapRef = useRef<L.Map | null>(null);
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const markersRef = useRef<Map<string, L.Marker>>(new Map());
    const currentLocationMarkerRef = useRef<L.Marker | null>(null);

    // Initialize map
    useEffect(() => {
        if (!mapContainerRef.current || mapRef.current) return;

        const map = L.map(mapContainerRef.current, {
            center: [12.9716, 77.5946], // Bangalore default
            zoom: 13,
            zoomControl: true,
        });

        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19,
        }).addTo(map);

        mapRef.current = map;

        return () => {
            map.remove();
            mapRef.current = null;
        };
    }, []);

    // Update current location marker
    useEffect(() => {
        if (!mapRef.current || !currentLocation) return;

        const map = mapRef.current;

        // Remove old marker
        if (currentLocationMarkerRef.current) {
            currentLocationMarkerRef.current.remove();
        }

        // Create custom current location icon
        const currentIcon = L.divIcon({
            className: 'map-marker-current',
            html: `
        <div class="map-marker-current__container">
          <div class="map-marker-current__pulse"></div>
          <div class="map-marker-current__dot"></div>
        </div>
      `,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
        });

        // Add new marker
        const marker = L.marker(
            [currentLocation.latitude, currentLocation.longitude],
            { icon: currentIcon }
        ).addTo(map);

        marker.bindPopup('Your Location');
        currentLocationMarkerRef.current = marker;

        // Center map on current location
        map.setView([currentLocation.latitude, currentLocation.longitude], map.getZoom());
    }, [currentLocation]);

    // Update hazard markers
    useEffect(() => {
        if (!mapRef.current) return;

        const map = mapRef.current;
        const currentMarkers = new Set<string>();

        hazards.forEach((hazard) => {
            currentMarkers.add(hazard.id);

            // Skip if marker already exists
            if (markersRef.current.has(hazard.id)) {
                return;
            }

            // Create custom hazard icon
            const icon = L.divIcon({
                className: `map-marker-hazard map-marker-hazard--${hazard.severity}`,
                html: `
          <div class="map-marker-hazard__container">
            <div class="map-marker-hazard__icon">
              ${getHazardIcon(hazard.hazardType)}
            </div>
          </div>
        `,
                iconSize: [32, 32],
                iconAnchor: [16, 32],
            });

            // Create marker
            const marker = L.marker(
                [hazard.location.latitude, hazard.location.longitude],
                { icon }
            ).addTo(map);

            // Add popup
            marker.bindPopup(`
        <div class="map-popup">
          <h4 class="map-popup__title">${formatHazardType(hazard.hazardType)}</h4>
          <div class="map-popup__details">
            <span class="map-popup__badge map-popup__badge--${hazard.severity}">
              ${hazard.severity}
            </span>
            <span class="map-popup__confidence">
              ${Math.round(hazard.confidence * 100)}% confident
            </span>
          </div>
          <p class="map-popup__time">
            ${new Date(hazard.detectedAt).toLocaleString()}
          </p>
        </div>
      `);

            // Handle click
            marker.on('click', () => {
                if (onHazardSelect) {
                    onHazardSelect(hazard);
                }
            });

            markersRef.current.set(hazard.id, marker);
        });

        // Remove markers for hazards that no longer exist
        markersRef.current.forEach((marker, id) => {
            if (!currentMarkers.has(id)) {
                marker.remove();
                markersRef.current.delete(id);
            }
        });
    }, [hazards, onHazardSelect]);

    // Highlight selected hazard
    useEffect(() => {
        if (!mapRef.current || !selectedHazard) return;

        const marker = markersRef.current.get(selectedHazard.id);
        if (marker) {
            marker.openPopup();
            mapRef.current.setView(
                [selectedHazard.location.latitude, selectedHazard.location.longitude],
                16
            );
        }
    }, [selectedHazard]);

    return (
        <div className={`map-panel ${className}`}>
            <div ref={mapContainerRef} className="map-panel__container" />

            {hazards.length === 0 && (
                <div className="map-panel__empty">
                    <svg className="map-panel__empty-icon" viewBox="0 0 24 24" fill="none">
                        <path
                            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                    <p className="map-panel__empty-text">No hazards detected yet</p>
                </div>
            )}
        </div>
    );
}

/**
 * Get SVG icon for hazard type
 */
function getHazardIcon(type: string): string {
    const icons: Record<string, string> = {
        pothole: `<svg viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="4"/>
    </svg>`,
        speed_hump: `<svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M2 12h20M6 8l6-4 6 4"/>
    </svg>`,
        crack: `<svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
    </svg>`,
        debris: `<svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
    </svg>`,
        other: `<svg viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="10"/>
    </svg>`,
    };
    return icons[type] || icons.other;
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
