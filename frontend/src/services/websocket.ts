/**
 * PaveX WebSocket Service
 * Handles real-time alerts and system status updates
 * FIXED: Properly handles backend alert format
 */

import type { Alert, WSMessage } from '../types';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000';

type MessageHandler = (message: WSMessage) => void;
type ConnectionHandler = (connected: boolean) => void;

class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private messageHandlers: Set<MessageHandler> = new Set();
    private connectionHandlers: Set<ConnectionHandler> = new Set();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 10;
    private reconnectDelay = 1000; // Start with 1 second
    private isIntentionallyClosed = false;

    constructor() {
        // Auto-connect on instantiation
        this.connect();
    }

    /**
     * Connect to WebSocket server
     */
    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        this.isIntentionallyClosed = false;

        try {
            this.ws = new WebSocket(`${WS_BASE_URL}/ws/alerts`);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.notifyConnectionHandlers(true);
            };

            this.ws.onmessage = (event) => {
                try {
                    const message: WSMessage = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.notifyConnectionHandlers(false);
                this.ws = null;

                // Attempt to reconnect if not intentionally closed
                if (!this.isIntentionallyClosed) {
                    this.scheduleReconnect();
                }
            };
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect(): void {
        this.isIntentionallyClosed = true;

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.notifyConnectionHandlers(false);
    }

    /**
     * Schedule reconnection attempt
     */
    private scheduleReconnect(): void {
        if (this.reconnectTimer) {
            return;
        }

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 30000);

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, delay);
    }

    /**
     * Handle incoming message
     * FIXED: Transform backend format to frontend Alert type
     */
    private handleMessage(message: WSMessage): void {
        // Transform backend hazard_alert to frontend Alert format
        if (message.type === 'hazard_alert' && message.data) {
            const backendAlert = message.data;

            // Convert backend format to frontend Alert
            const frontendAlert: Alert = {
                id: backendAlert.id || crypto.randomUUID(),
                hazardType: backendAlert.hazard_type || backendAlert.hazardType,
                severity: backendAlert.severity,
                message: backendAlert.message || this.generateAlertMessage(backendAlert),
                location: {
                    latitude: backendAlert.location?.latitude || backendAlert.latitude,
                    longitude: backendAlert.location?.longitude || backendAlert.longitude,
                },
                distance: backendAlert.distance,
                timestamp: backendAlert.timestamp || message.timestamp || new Date().toISOString(),
                acknowledged: false,
            };

            // Create transformed message
            const transformedMessage: WSMessage = {
                type: 'hazard_alert',
                data: frontendAlert,
                timestamp: message.timestamp,
            };

            this.notifyMessageHandlers(transformedMessage);
        } else {
            // Pass through other message types
            this.notifyMessageHandlers(message);
        }
    }

    /**
     * Generate alert message from backend data
     */
    private generateAlertMessage(data: any): string {
        const hazardName = data.hazard_type || data.hazardType || 'hazard';
        const severity = data.severity || 'unknown';
        const distance = data.distance ? ` ${Math.round(data.distance)}m ahead` : '';

        return `${severity.toUpperCase()} ${hazardName.replace('_', ' ')} detected${distance}`;
    }

    /**
     * Send message to server
     */
    send(message: any): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }

    /**
     * Subscribe to messages
     */
    onMessage(handler: MessageHandler): () => void {
        this.messageHandlers.add(handler);

        // Return unsubscribe function
        return () => {
            this.messageHandlers.delete(handler);
        };
    }

    /**
     * Subscribe to connection status
     */
    onConnectionChange(handler: ConnectionHandler): () => void {
        this.connectionHandlers.add(handler);

        // Immediately notify of current status
        const isConnected = this.ws?.readyState === WebSocket.OPEN;
        handler(isConnected);

        // Return unsubscribe function
        return () => {
            this.connectionHandlers.delete(handler);
        };
    }

    /**
     * Notify all message handlers
     */
    private notifyMessageHandlers(message: WSMessage): void {
        this.messageHandlers.forEach(handler => {
            try {
                handler(message);
            } catch (error) {
                console.error('Message handler error:', error);
            }
        });
    }

    /**
     * Notify all connection handlers
     */
    private notifyConnectionHandlers(connected: boolean): void {
        this.connectionHandlers.forEach(handler => {
            try {
                handler(connected);
            } catch (error) {
                console.error('Connection handler error:', error);
            }
        });
    }

    /**
     * Get connection status
     */
    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }

    /**
     * Get ready state
     */
    getReadyState(): number {
        return this.ws?.readyState ?? WebSocket.CLOSED;
    }
}

// Export singleton instance
export const websocket = new WebSocketService();

// Export class for testing
export default WebSocketService;
