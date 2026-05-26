'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

interface AlarmEvent {
  alarm_id: string;
  olt_id?: string;
  olt_name?: string;
  onu_id?: string;
  onu_serial?: string;
  type: string;
  severity: string;
  message: string;
  raised_at: string;
}

interface SocketContextType {
  isConnected: boolean;
  latestEvent: any;
  activeAlarms: AlarmEvent[];
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [latestEvent, setLatestEvent] = useState<any>(null);
  const [activeAlarms, setActiveAlarms] = useState<AlarmEvent[]>([]);

  // Load active alarms from REST API on load
  useEffect(() => {
    if (token) {
      // In a real app we'd trigger a fetch here. Let's do that once layout loads
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;

    let socket: WebSocket;
    let reconnectTimeout: any;

    const connect = () => {
      // Fetch relative host WS endpoint
      const wsUrl = `ws://${window.location.host}/ws`;
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setIsConnected(true);
        console.log('NOC WebSockets: Connected successfully');
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setLatestEvent(payload);

          // Handle live alarms
          if (payload.event === 'alarm_raised') {
            const newAlarm: AlarmEvent = payload.data;
            setActiveAlarms((prev) => [newAlarm, ...prev.filter(a => a.alarm_id !== newAlarm.alarm_id)]);
            playAlertSound(newAlarm.severity);
          } else if (payload.event === 'alarm_cleared') {
            const clearedId = payload.data.alarm_id;
            setActiveAlarms((prev) => prev.filter((a) => a.alarm_id !== clearedId));
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        console.log('NOC WebSockets: Connection closed, retrying...');
        reconnectTimeout = setTimeout(connect, 3000); // Reconnect in 3s
      };

      socket.onerror = (err) => {
        console.error('WebSocket Error:', err);
        socket.close();
      };
    };

    connect();

    return () => {
      if (socket) socket.close();
      clearTimeout(reconnectTimeout);
    };
  }, [token]);

  // Audio synthesizer using Web Audio API to alert operators
  const playAlertSound = (severity: string) => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      if (severity === 'CRITICAL') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, ctx.currentTime); // High alarm pitch
        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        osc.start();
        osc.stop(ctx.currentTime + 0.3);
      } else {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, ctx.currentTime); // Normal warning pitch
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
      }
    } catch (e) {
      console.warn('AudioContext alert playback blocked by browser user-interaction rules', e);
    }
  };

  return (
    <SocketContext.Provider value={{ isConnected, latestEvent, activeAlarms }}>
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
}
