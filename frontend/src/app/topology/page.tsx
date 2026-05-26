'use client';

import React, { useState, useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import axios from 'axios';
import { Server, Compass, Layers } from 'lucide-react';
import dynamic from 'next/dynamic';

// Import leaflet styles
import 'leaflet/dist/leaflet.css';

// Dynamically import Leaflet components to avoid SSR 'window is not defined' errors in Next.js
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);
const Marker = dynamic(
  () => import('react-leaflet').then((mod) => mod.Marker),
  { ssr: false }
);
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
);
const Polyline = dynamic(
  () => import('react-leaflet').then((mod) => mod.Polyline),
  { ssr: false }
);

interface OLT {
  id: string;
  name: string;
  ip_address: string;
  vendor: string;
  status: string;
  pop_name: string | null;
  latitude: number | null;
  longitude: number | null;
}

export default function TopologyPage() {
  const [olts, setOlts] = useState<OLT[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [leafletIcon, setLeafletIcon] = useState<any>(null);

  // Default focus coordinates (DHAKA/ISP main hub default)
  const defaultCenter: [number, number] = [23.8103, 90.4125];

  useEffect(() => {
    const fetchOlts = async () => {
      try {
        const res = await axios.get('/api/v1/olts/');
        setOlts(res.data);
      } catch (err) {
        console.error('Error fetching OLT coordinates:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchOlts();

    // Create custom leaflet marker icon on client side
    if (typeof window !== 'undefined') {
      import('leaflet').then((L) => {
        const customIcon = L.icon({
          iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
          shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41]
        });
        setLeafletIcon(customIcon);
      });
    }
  }, []);

  // Filter out OLTs that have valid latitude/longitude coordinates
  const mappedOlts = olts.filter(o => o.latitude !== null && o.longitude !== null);

  return (
    <DashboardLayout>
      <div className="space-y-6 flex flex-col h-[85vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-white">GIS Topology Mapping</h1>
            <p className="text-xs text-noc-textMuted mt-1">Geographical distribution of OLT POP sites and main fiber trunk connections.</p>
          </div>
        </div>

        {/* 1. Map container panel */}
        <div className="flex-1 rounded-xl overflow-hidden glass-panel border border-noc-border flex flex-col">
          
          <div className="p-4 bg-[#0C1221] border-b border-noc-border flex items-center justify-between text-xs">
            <div className="flex items-center gap-6">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400 status-glow-green" /> ONLINE OLT</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-400 status-glow-red" /> OFFLINE OLT</span>
              <span className="flex items-center gap-1.5 text-indigo-400"><span className="w-4 h-0.5 bg-indigo-500 inline-block align-middle mr-1" /> Backbone Fiber</span>
            </div>
            <span className="font-mono text-noc-textMuted uppercase text-[10px]">Active Node Markers: {mappedOlts.length}</span>
          </div>

          <div className="flex-1 w-full bg-[#0B0F19] relative z-0">
            {isLoading ? (
              <div className="absolute inset-0 flex items-center justify-center font-mono text-xs text-noc-textMuted animate-pulse">
                Loading GIS maps mapping layer...
              </div>
            ) : typeof window === 'undefined' || !leafletIcon ? (
              <div className="absolute inset-0 flex items-center justify-center font-mono text-xs text-noc-textMuted">
                Initializing maps module...
              </div>
            ) : (
              <MapContainer 
                center={mappedOlts.length > 0 ? [mappedOlts[0].latitude!, mappedOlts[0].longitude!] : defaultCenter} 
                zoom={12} 
                style={{ height: '100%', width: '100%', filter: 'invert(90%) hue-rotate(180deg)' }} // Cool dark-mode map filter!
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                {/* Draw OLT Markers */}
                {mappedOlts.map((olt) => (
                  <Marker 
                    key={olt.id} 
                    position={[olt.latitude!, olt.longitude!]}
                    icon={leafletIcon}
                  >
                    <Popup>
                      <div className="p-2 font-sans text-xs text-gray-800 space-y-1">
                        <strong className="block text-sm border-b pb-1 mb-1">{olt.name}</strong>
                        <span>IP: <strong className="font-mono">{olt.ip_address}</strong></span>
                        <span className="block">Vendor: <strong className="uppercase">{olt.vendor}</strong></span>
                        <span className="block">POP: <strong>{olt.pop_name || 'N/A'}</strong></span>
                        <span className="block mt-1 font-semibold">
                          Status: 
                          <span className={olt.status === 'ONLINE' ? 'text-emerald-600 ml-1' : 'text-rose-600 ml-1'}>
                            {olt.status}
                          </span>
                        </span>
                      </div>
                    </Popup>
                  </Marker>
                ))}

                {/* Draw Backbone Simulated fiber lines connecting OLTs together to show routing routes */}
                {mappedOlts.length > 1 && (
                  <Polyline 
                    positions={mappedOlts.map(o => [o.latitude!, o.longitude!]) as [number, number][]}
                    pathOptions={{ color: '#6366F1', weight: 3, dashArray: '8, 8', lineCap: 'round' }}
                  />
                )}
              </MapContainer>
            )}
          </div>

        </div>

      </div>
    </DashboardLayout>
  );
}
